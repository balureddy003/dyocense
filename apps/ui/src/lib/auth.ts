export interface KeycloakEnvConfig {
  url?: string;
  realm?: string;
  clientId?: string;
}

const config: KeycloakEnvConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL,
  realm: import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
};

export const getKeycloakConfig = () => config;

export const isKeycloakConfigured = (): boolean => {
  return Boolean(config.url && config.realm && config.clientId);
};
