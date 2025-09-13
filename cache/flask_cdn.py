"""
Flask extension for CDN integration.
"""

import os
import logging
from typing import Dict, Any, Optional
from flask import Flask, current_app, g, request, url_for
try:
    import click
except ImportError:
    click = None
try:
    from jinja2 import Markup
except ImportError:
    from markupsafe import Markup

from .cdn import CDNManager, AssetVersionManager, init_cdn

logger = logging.getLogger(__name__)


class FlaskCDN:
    """Flask extension for CDN integration."""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.cdn_manager = None
        self.asset_version_manager = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the CDN extension with Flask app."""
        self.app = app
        
        # Load CDN configuration
        cdn_config = self._load_cdn_config(app)
        
        # Initialize CDN manager
        redis_client = getattr(app, 'cache', None)
        if redis_client and hasattr(redis_client, 'redis_client'):
            redis_client = redis_client.redis_client
        
        self.cdn_manager = init_cdn(cdn_config, redis_client)
        
        # Register template functions
        self._register_template_functions(app)
        
        # Register CLI commands
        self._register_cli_commands(app)
        
        # Add CDN manager to app
        app.cdn = self.cdn_manager
        
        # Set up request context processors
        self._setup_context_processors(app)
        
        logger.info("Flask CDN extension initialized")
    
    def _load_cdn_config(self, app: Flask) -> Dict[str, Any]:
        """Load CDN configuration from app config and files."""
        config = {}
        
        # Load from app config
        config.update(app.config.get('CDN', {}))
        
        # Load from YAML file if exists
        config_file = os.path.join(app.root_path, 'config', 'cdn.yaml')
        if os.path.exists(config_file):
            try:
                import yaml
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                
                # Merge environment-specific config
                env = app.config.get('ENV', 'development')
                if 'environments' in file_config and env in file_config['environments']:
                    env_config = file_config['environments'][env]
                    # Deep merge environment config
                    self._deep_merge(file_config, env_config)
                
                # Merge with existing config
                self._deep_merge(config, file_config.get('cdn', {}))
                
            except Exception as e:
                logger.warning(f"Failed to load CDN config from YAML: {e}")
        
        # Override with environment variables
        env_overrides = {
            'enabled': os.getenv('CDN_ENABLED', '').lower() == 'true',
            'provider': os.getenv('CDN_PROVIDER'),
            'base_url': os.getenv('CDN_BASE_URL'),
            'distribution_id': os.getenv('CDN_DISTRIBUTION_ID'),
            's3_bucket': os.getenv('CDN_S3_BUCKET'),
            'aws_region': os.getenv('CDN_AWS_REGION')
        }
        
        # Apply non-empty environment overrides
        for key, value in env_overrides.items():
            if value:
                config[key] = value
        
        return config
    
    def _deep_merge(self, base_dict: Dict, update_dict: Dict):
        """Deep merge two dictionaries."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _register_template_functions(self, app: Flask):
        """Register CDN template functions."""
        
        @app.template_global()
        def cdn_url_for(endpoint: str, **values) -> str:
            """Generate CDN URL for static assets in templates."""
            if endpoint == 'static' and self.cdn_manager and self.cdn_manager.is_enabled():
                filename = values.get('filename')
                if filename:
                    return self.cdn_manager.get_asset_url(filename)
            
            # Fallback to regular url_for
            return url_for(endpoint, **values)
        
        @app.template_global()
        def asset_url(asset_path: str, version: Optional[str] = None) -> str:
            """Generate asset URL with optional versioning."""
            if self.cdn_manager and self.cdn_manager.is_enabled():
                return self.cdn_manager.get_asset_url(asset_path, version)
            
            # Local URL with versioning
            if version:
                return url_for('static', filename=f"{asset_path}?v={version}")
            
            return url_for('static', filename=asset_path)
        
        @app.template_global()
        def preload_asset(asset_path: str, as_type: str = 'script') -> Markup:
            """Generate preload link tag for critical assets."""
            asset_url_str = asset_url(asset_path)
            return Markup(f'<link rel="preload" href="{asset_url_str}" as="{as_type}">')
        
        @app.template_global()
        def dns_prefetch(domain: str) -> Markup:
            """Generate DNS prefetch link tag."""
            return Markup(f'<link rel="dns-prefetch" href="//{domain}">')
        
        @app.template_global()
        def preconnect(domain: str) -> Markup:
            """Generate preconnect link tag."""
            return Markup(f'<link rel="preconnect" href="https://{domain}" crossorigin>')
        
        @app.template_filter()
        def versioned(asset_path: str) -> str:
            """Add version parameter to asset path."""
            if self.asset_version_manager:
                version = self.asset_version_manager.get_version(asset_path)
                if version:
                    return f"{asset_path}?v={version}"
            return asset_path
    
    def _register_cli_commands(self, app: Flask):
        """Register CDN CLI commands."""
        
        # Only register CLI commands if click is available
        if click is None or not hasattr(app, 'cli'):
            logger.warning("Flask CLI or click not available, skipping CDN CLI commands")
            return
        
        @app.cli.group()
        def cdn():
            """CDN management commands."""
            pass
        
        @cdn.command()
        def status():
            """Show CDN status and configuration."""
            if not self.cdn_manager:
                print("CDN not initialized")
                return
            
            print(f"CDN Enabled: {self.cdn_manager.is_enabled()}")
            print(f"Provider: {self.cdn_manager.provider}")
            print(f"Base URL: {self.cdn_manager.base_url}")
            
            if self.cdn_manager.is_enabled():
                stats = self.cdn_manager.get_distribution_stats()
                if 'error' not in stats:
                    print(f"Distribution ID: {stats.get('distribution_id')}")
                    print(f"Domain Name: {stats.get('domain_name')}")
                    print(f"Status: {stats.get('status')}")
                else:
                    print(f"Error getting stats: {stats['error']}")
        
        @cdn.command()
        def sync():
            """Sync static assets to CDN."""
            if not self.cdn_manager or not self.cdn_manager.is_enabled():
                print("CDN not enabled")
                return
            
            static_folder = app.static_folder
            if not static_folder:
                print("No static folder configured")
                return
            
            print(f"Syncing assets from {static_folder}...")
            results = self.cdn_manager.sync_static_assets(static_folder)
            
            print(f"Upload results:")
            print(f"  Uploaded: {results['uploaded']}")
            print(f"  Skipped: {results['skipped']}")
            print(f"  Failed: {results['failed']}")
            
            if results.get('error'):
                print(f"Error: {results['error']}")
        
        @cdn.command()
        @click.argument('paths', nargs=-1)
        def invalidate(paths):
            """Invalidate CDN cache for specified paths."""
            if not self.cdn_manager or not self.cdn_manager.is_enabled():
                print("CDN not enabled")
                return
            
            if not paths:
                print("No paths specified")
                return
            
            print(f"Invalidating {len(paths)} paths...")
            success = self.cdn_manager.invalidate_cache(list(paths))
            
            if success:
                print("Cache invalidation initiated successfully")
            else:
                print("Failed to initiate cache invalidation")
        
        @cdn.command()
        def test():
            """Test CDN connectivity and configuration."""
            if not self.cdn_manager:
                print("CDN not initialized")
                return
            
            print("Testing CDN configuration...")
            
            # Test basic configuration
            print(f"✓ CDN Manager initialized")
            print(f"✓ Provider: {self.cdn_manager.provider}")
            print(f"✓ Base URL: {self.cdn_manager.base_url or 'Not configured'}")
            
            if self.cdn_manager.is_enabled():
                # Test asset URL generation
                test_asset = "css/main.css"
                asset_url = self.cdn_manager.get_asset_url(test_asset)
                print(f"✓ Asset URL generation: {asset_url}")
                
                # Test distribution stats
                stats = self.cdn_manager.get_distribution_stats()
                if 'error' not in stats:
                    print(f"✓ Distribution accessible: {stats.get('status')}")
                else:
                    print(f"✗ Distribution error: {stats['error']}")
            else:
                print("ℹ CDN disabled or not configured")
    
    def _setup_context_processors(self, app: Flask):
        """Set up request context processors for CDN."""
        
        @app.context_processor
        def inject_cdn_context():
            """Inject CDN-related variables into template context."""
            return {
                'cdn_enabled': self.cdn_manager.is_enabled() if self.cdn_manager else False,
                'cdn_base_url': self.cdn_manager.base_url if self.cdn_manager else '',
            }
        
        @app.before_request
        def setup_cdn_context():
            """Set up CDN context for the request."""
            g.cdn_enabled = self.cdn_manager.is_enabled() if self.cdn_manager else False
            g.cdn_manager = self.cdn_manager


class CDNBlueprint:
    """Blueprint for CDN management endpoints."""
    
    def __init__(self, cdn_extension: FlaskCDN):
        self.cdn_extension = cdn_extension
    
    def create_blueprint(self):
        """Create Flask blueprint for CDN endpoints."""
        from flask import Blueprint, jsonify, request
        
        bp = Blueprint('cdn', __name__, url_prefix='/api/cdn')
        
        @bp.route('/status')
        def status():
            """Get CDN status and statistics."""
            if not self.cdn_extension.cdn_manager:
                return jsonify({'error': 'CDN not initialized'}), 500
            
            manager = self.cdn_extension.cdn_manager
            
            status_info = {
                'enabled': manager.is_enabled(),
                'provider': manager.provider,
                'base_url': manager.base_url,
                'config': {
                    'auto_version': manager.config.get('auto_version', False),
                    'distribution_id': manager.distribution_id,
                    's3_bucket': manager.s3_bucket
                }
            }
            
            if manager.is_enabled():
                stats = manager.get_distribution_stats()
                status_info['distribution'] = stats
            
            return jsonify(status_info)
        
        @bp.route('/sync', methods=['POST'])
        def sync_assets():
            """Sync static assets to CDN."""
            if not self.cdn_extension.cdn_manager or not self.cdn_extension.cdn_manager.is_enabled():
                return jsonify({'error': 'CDN not enabled'}), 400
            
            static_folder = current_app.static_folder
            if not static_folder:
                return jsonify({'error': 'No static folder configured'}), 400
            
            results = self.cdn_extension.cdn_manager.sync_static_assets(static_folder)
            return jsonify(results)
        
        @bp.route('/invalidate', methods=['POST'])
        def invalidate_cache():
            """Invalidate CDN cache for specified paths."""
            if not self.cdn_extension.cdn_manager or not self.cdn_extension.cdn_manager.is_enabled():
                return jsonify({'error': 'CDN not enabled'}), 400
            
            data = request.get_json()
            paths = data.get('paths', [])
            
            if not paths:
                return jsonify({'error': 'No paths specified'}), 400
            
            success = self.cdn_extension.cdn_manager.invalidate_cache(paths)
            
            if success:
                return jsonify({'message': 'Cache invalidation initiated', 'paths': paths})
            else:
                return jsonify({'error': 'Failed to initiate cache invalidation'}), 500
        
        @bp.route('/asset-url')
        def get_asset_url():
            """Get CDN URL for an asset."""
            asset_path = request.args.get('path')
            version = request.args.get('version')
            
            if not asset_path:
                return jsonify({'error': 'Asset path required'}), 400
            
            if self.cdn_extension.cdn_manager and self.cdn_extension.cdn_manager.is_enabled():
                url = self.cdn_extension.cdn_manager.get_asset_url(asset_path, version)
            else:
                url = url_for('static', filename=asset_path)
                if version:
                    url += f"?v={version}"
            
            return jsonify({
                'asset_path': asset_path,
                'url': url,
                'cdn_enabled': self.cdn_extension.cdn_manager.is_enabled() if self.cdn_extension.cdn_manager else False
            })
        
        return bp


def create_cdn_extension(app: Flask = None) -> FlaskCDN:
    """Factory function to create CDN extension."""
    return FlaskCDN(app)