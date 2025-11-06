import React from 'react';
import { Info, Zap } from 'lucide-react';

interface DeploymentModeBannerProps {
  mode?: 'smb' | 'platform';
}

export const DeploymentModeBanner: React.FC<DeploymentModeBannerProps> = ({ mode = 'smb' }) => {
  // In production, this would come from an API or environment variable
  const deploymentMode = mode;

  if (deploymentMode === 'smb') {
    // SMB mode - show nothing or subtle indicator
    return null;
  }

  // Platform mode - show enterprise features banner
  return (
    <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white py-2 px-4">
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-sm">
        <Zap size={16} className="animate-pulse" />
        <span className="font-medium">
          Platform Mode: Enterprise features enabled (Evidence Graph, Vector Search, SSO)
        </span>
      </div>
    </div>
  );
};

interface FeatureGateBadgeProps {
  requiresPlatformMode?: boolean;
  children: React.ReactNode;
}

export const FeatureGateBadge: React.FC<FeatureGateBadgeProps> = ({ 
  requiresPlatformMode = false,
  children 
}) => {
  if (!requiresPlatformMode) {
    return <>{children}</>;
  }

  return (
    <div className="relative inline-block group">
      {children}
      <div className="absolute -top-2 -right-2 z-10">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-700 border border-purple-200">
          <Info size={10} />
          Enterprise
        </span>
      </div>
      <div className="absolute hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap z-20">
        Available in Enterprise tier ($1999+/mo)
        <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
      </div>
    </div>
  );
};
