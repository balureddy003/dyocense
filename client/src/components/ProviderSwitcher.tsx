import { useEffect } from 'react';
import { fetchProviders, Provider } from '../services/api';
import { useChatStore } from '../store/chatStore';

interface ProviderSwitcherProps {
  providers: Provider[];
  setProviders: (providers: Provider[]) => void;
}

export function ProviderSwitcher({ providers, setProviders }: ProviderSwitcherProps) {
  const { providerId, setProvider, loading } = useChatStore();

  useEffect(() => {
    fetchProviders()
      .then(setProviders)
      .catch(() => setProviders([]));
  }, [setProviders]);

  useEffect(() => {
    if (providers.length && !providers.some((provider) => provider.provider_id === providerId)) {
      setProvider(providers[0].provider_id);
    }
  }, [providers, providerId, setProvider]);

  return (
    <div className="provider-switcher">
      <h3>LLM Provider</h3>
      <div className="provider-list">
        {providers.map((provider) => (
          <button
            key={provider.provider_id}
            type="button"
            className={provider.provider_id === providerId ? 'active' : ''}
            onClick={() => setProvider(provider.provider_id)}
            disabled={loading}
          >
            <strong>{provider.name}</strong>
            <span>{provider.model}</span>
          </button>
        ))}
        {providers.length === 0 && <span style={{ color: 'rgba(255,255,255,0.6)' }}>No providers configured.</span>}
      </div>
    </div>
  );
}
