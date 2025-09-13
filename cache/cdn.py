"""
CDN integration for static asset delivery and performance optimization.
"""

import os
import logging
import hashlib
import mimetypes
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta

from flask import current_app, url_for, request
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class CDNManager:
    """Manage CDN integration for static assets."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', False)
        self.provider = self.config.get('provider', 'cloudfront')
        self.base_url = self.config.get('base_url', '')
        self.cache_control_rules = self.config.get('cache_control', {})
        
        # AWS CloudFront specific settings
        self.distribution_id = self.config.get('distribution_id')
        self.s3_bucket = self.config.get('s3_bucket')
        self.aws_region = self.config.get('aws_region', 'us-east-1')
        
        # Initialize AWS clients if using CloudFront
        self.cloudfront_client = None
        self.s3_client = None
        
        if self.enabled and self.provider == 'cloudfront':
            self._init_aws_clients()
    
    def _init_aws_clients(self):
        """Initialize AWS clients for CloudFront and S3."""
        try:
            # Use environment variables or IAM roles for credentials
            self.cloudfront_client = boto3.client('cloudfront', region_name=self.aws_region)
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
            
            # Test connection
            self.cloudfront_client.list_distributions(MaxItems='1')
            logger.info("AWS CloudFront client initialized successfully")
            
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"Failed to initialize AWS clients: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if CDN is enabled and properly configured."""
        return self.enabled and bool(self.base_url)
    
    def get_asset_url(self, asset_path: str, version: Optional[str] = None) -> str:
        """Get CDN URL for static asset."""
        if not self.is_enabled():
            # Return local URL if CDN is disabled
            return url_for('static', filename=asset_path)
        
        # Clean asset path
        asset_path = asset_path.lstrip('/')
        
        # Add version parameter for cache busting
        if version:
            asset_path = f"{asset_path}?v={version}"
        elif self.config.get('auto_version', True):
            # Generate version based on file modification time or content hash
            version = self._get_asset_version(asset_path)
            if version:
                asset_path = f"{asset_path}?v={version}"
        
        # Construct CDN URL
        cdn_url = urljoin(self.base_url.rstrip('/') + '/', asset_path)
        return cdn_url
    
    def _get_asset_version(self, asset_path: str) -> Optional[str]:
        """Get version string for asset (based on modification time or content hash)."""
        try:
            # Try to get local file info for versioning
            static_folder = current_app.static_folder
            if static_folder:
                file_path = os.path.join(static_folder, asset_path.split('?')[0])
                if os.path.exists(file_path):
                    # Use file modification time as version
                    mtime = os.path.getmtime(file_path)
                    return str(int(mtime))
            
            # Fallback to app version or timestamp
            return current_app.config.get('VERSION', str(int(datetime.utcnow().timestamp())))
            
        except Exception as e:
            logger.debug(f"Failed to get asset version for {asset_path}: {e}")
            return None
    
    def upload_asset(self, local_path: str, cdn_path: str, 
                    content_type: Optional[str] = None) -> bool:
        """Upload asset to CDN storage (S3 for CloudFront)."""
        if not self.is_enabled() or self.provider != 'cloudfront' or not self.s3_bucket:
            return False
        
        try:
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(local_path)
                content_type = content_type or 'application/octet-stream'
            
            # Get cache control settings
            cache_control = self._get_cache_control(cdn_path, content_type)
            
            # Upload to S3
            with open(local_path, 'rb') as file_data:
                extra_args = {
                    'ContentType': content_type,
                    'CacheControl': cache_control,
                    'ACL': 'public-read'
                }
                
                # Add compression for text files
                if content_type.startswith(('text/', 'application/javascript', 'application/json')):
                    extra_args['ContentEncoding'] = 'gzip'
                
                self.s3_client.upload_fileobj(
                    file_data,
                    self.s3_bucket,
                    cdn_path,
                    ExtraArgs=extra_args
                )
            
            logger.info(f"Successfully uploaded {local_path} to CDN as {cdn_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload asset to CDN: {e}")
            return False
    
    def _get_cache_control(self, file_path: str, content_type: str) -> str:
        """Get cache control header based on file type and configuration."""
        # Default cache control
        default_cache = "public, max-age=3600"  # 1 hour
        
        # Check for specific rules
        for pattern, cache_rule in self.cache_control_rules.items():
            if pattern in file_path or pattern in content_type:
                return cache_rule
        
        # Content type based rules
        if content_type.startswith('image/'):
            return "public, max-age=86400, immutable"  # 24 hours for images
        elif content_type in ['text/css', 'application/javascript']:
            return "public, max-age=31536000, immutable"  # 1 year for CSS/JS
        elif content_type.startswith('font/'):
            return "public, max-age=31536000, immutable"  # 1 year for fonts
        elif content_type.startswith('text/html'):
            return "public, max-age=300"  # 5 minutes for HTML
        
        return default_cache
    
    def invalidate_cache(self, paths: List[str]) -> bool:
        """Invalidate CDN cache for specified paths."""
        if not self.is_enabled() or self.provider != 'cloudfront' or not self.distribution_id:
            return False
        
        try:
            # Prepare paths for CloudFront invalidation
            invalidation_paths = []
            for path in paths:
                if not path.startswith('/'):
                    path = '/' + path
                invalidation_paths.append(path)
            
            # Create invalidation
            response = self.cloudfront_client.create_invalidation(
                DistributionId=self.distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(invalidation_paths),
                        'Items': invalidation_paths
                    },
                    'CallerReference': f"invalidation-{int(datetime.utcnow().timestamp())}"
                }
            )
            
            invalidation_id = response['Invalidation']['Id']
            logger.info(f"Created CloudFront invalidation {invalidation_id} for {len(paths)} paths")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate CDN cache: {e}")
            return False
    
    def get_distribution_stats(self) -> Dict[str, Any]:
        """Get CDN distribution statistics."""
        if not self.is_enabled() or self.provider != 'cloudfront' or not self.distribution_id:
            return {'error': 'CDN not properly configured'}
        
        try:
            # Get distribution info
            response = self.cloudfront_client.get_distribution(Id=self.distribution_id)
            distribution = response['Distribution']
            
            # Get distribution config
            config = distribution['DistributionConfig']
            
            stats = {
                'distribution_id': self.distribution_id,
                'domain_name': distribution['DomainName'],
                'status': distribution['Status'],
                'enabled': config['Enabled'],
                'price_class': config['PriceClass'],
                'origins': len(config['Origins']['Items']),
                'cache_behaviors': len(config['CacheBehaviors']['Items']) + 1,  # +1 for default
                'last_modified': distribution['LastModifiedTime'].isoformat(),
                'base_url': self.base_url
            }
            
            # Get recent invalidations
            try:
                invalidations = self.cloudfront_client.list_invalidations(
                    DistributionId=self.distribution_id,
                    MaxItems='5'
                )
                stats['recent_invalidations'] = [
                    {
                        'id': inv['Id'],
                        'status': inv['Status'],
                        'create_time': inv['CreateTime'].isoformat()
                    }
                    for inv in invalidations['InvalidationList']['Items']
                ]
            except Exception:
                stats['recent_invalidations'] = []
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get distribution stats: {e}")
            return {'error': str(e)}
    
    def sync_static_assets(self, static_folder: str) -> Dict[str, Any]:
        """Sync local static assets to CDN."""
        if not self.is_enabled() or not static_folder or not os.path.exists(static_folder):
            return {'error': 'CDN not enabled or static folder not found'}
        
        results = {
            'uploaded': 0,
            'skipped': 0,
            'failed': 0,
            'files': []
        }
        
        try:
            # Walk through static folder
            for root, dirs, files in os.walk(static_folder):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, static_folder)
                    cdn_path = relative_path.replace('\\', '/')  # Normalize path separators
                    
                    # Skip certain files
                    if self._should_skip_file(file):
                        results['skipped'] += 1
                        continue
                    
                    # Upload file
                    if self.upload_asset(local_path, cdn_path):
                        results['uploaded'] += 1
                        results['files'].append({
                            'path': cdn_path,
                            'status': 'uploaded',
                            'url': self.get_asset_url(cdn_path)
                        })
                    else:
                        results['failed'] += 1
                        results['files'].append({
                            'path': cdn_path,
                            'status': 'failed'
                        })
            
            logger.info(f"CDN sync completed: {results['uploaded']} uploaded, "
                       f"{results['skipped']} skipped, {results['failed']} failed")
            
        except Exception as e:
            logger.error(f"Error during CDN sync: {e}")
            results['error'] = str(e)
        
        return results
    
    def _should_skip_file(self, filename: str) -> bool:
        """Check if file should be skipped during sync."""
        skip_patterns = [
            '.DS_Store',
            'Thumbs.db',
            '.gitkeep',
            '.gitignore'
        ]
        
        skip_extensions = [
            '.tmp',
            '.bak',
            '.log'
        ]
        
        # Check patterns
        for pattern in skip_patterns:
            if pattern in filename:
                return True
        
        # Check extensions
        for ext in skip_extensions:
            if filename.endswith(ext):
                return True
        
        return False


class AssetVersionManager:
    """Manage asset versioning for cache busting."""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.version_key = 'asset_versions'
        self.global_version = None
    
    def get_version(self, asset_path: str) -> Optional[str]:
        """Get version for specific asset."""
        if self.redis_client and self.redis_client.is_available():
            try:
                version = self.redis_client.redis_client.hget(self.version_key, asset_path)
                return version.decode() if version else None
            except Exception as e:
                logger.debug(f"Failed to get asset version from Redis: {e}")
        
        return self.global_version
    
    def set_version(self, asset_path: str, version: str) -> bool:
        """Set version for specific asset."""
        if self.redis_client and self.redis_client.is_available():
            try:
                self.redis_client.redis_client.hset(self.version_key, asset_path, version)
                return True
            except Exception as e:
                logger.error(f"Failed to set asset version in Redis: {e}")
        
        return False
    
    def set_global_version(self, version: str):
        """Set global version for all assets."""
        self.global_version = version
        
        if self.redis_client and self.redis_client.is_available():
            try:
                self.redis_client.set('global_asset_version', version, 3600)  # 1 hour TTL
            except Exception as e:
                logger.debug(f"Failed to set global version in Redis: {e}")
    
    def generate_content_hash(self, file_path: str) -> Optional[str]:
        """Generate content hash for file."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()[:8]
        except Exception as e:
            logger.error(f"Failed to generate content hash for {file_path}: {e}")
            return None
    
    def update_versions_from_manifest(self, manifest_path: str) -> int:
        """Update asset versions from webpack manifest or similar."""
        try:
            import json
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            updated_count = 0
            for asset_path, versioned_path in manifest.items():
                # Extract version from versioned path
                if '?' in versioned_path:
                    version = versioned_path.split('?v=')[-1]
                elif '.' in versioned_path:
                    # Handle hash-based versioning like app.abc123.js
                    parts = versioned_path.split('.')
                    if len(parts) >= 3:
                        version = parts[-2]  # Get hash part
                    else:
                        continue
                else:
                    continue
                
                if self.set_version(asset_path, version):
                    updated_count += 1
            
            logger.info(f"Updated {updated_count} asset versions from manifest")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to update versions from manifest: {e}")
            return 0


# Global CDN manager instance
cdn_manager = None
asset_version_manager = None


def init_cdn(config: Dict[str, Any], redis_client=None):
    """Initialize CDN manager."""
    global cdn_manager, asset_version_manager
    
    cdn_manager = CDNManager(config)
    asset_version_manager = AssetVersionManager(redis_client)
    
    if cdn_manager.is_enabled():
        logger.info(f"CDN initialized with provider: {cdn_manager.provider}")
    else:
        logger.info("CDN disabled or not configured")
    
    return cdn_manager


def get_cdn_manager() -> Optional[CDNManager]:
    """Get the global CDN manager instance."""
    return cdn_manager


def get_asset_version_manager() -> Optional[AssetVersionManager]:
    """Get the global asset version manager instance."""
    return asset_version_manager


# Template helper functions
def cdn_url_for(endpoint: str, **values) -> str:
    """Generate CDN URL for static assets in templates."""
    if endpoint == 'static' and cdn_manager and cdn_manager.is_enabled():
        filename = values.get('filename')
        if filename:
            return cdn_manager.get_asset_url(filename)
    
    # Fallback to regular url_for
    return url_for(endpoint, **values)


def asset_url(asset_path: str, version: Optional[str] = None) -> str:
    """Generate asset URL with optional versioning."""
    if cdn_manager and cdn_manager.is_enabled():
        return cdn_manager.get_asset_url(asset_path, version)
    
    # Local URL with versioning
    if version:
        return url_for('static', filename=f"{asset_path}?v={version}")
    
    return url_for('static', filename=asset_path)