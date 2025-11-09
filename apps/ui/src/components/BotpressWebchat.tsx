import React, { useEffect } from "react";

interface BotpressWebchatProps {
    botId: string;
    userId?: string;
    extraParams?: Record<string, any>;
}

export const BotpressWebchat: React.FC<BotpressWebchatProps> = ({ botId, userId, extraParams }) => {
    useEffect(() => {
        if (document.getElementById("bp-web-widget")) return;
        const script = document.createElement("script");
        script.src = "https://cdn.botpress.cloud/webchat/v1/inject.js";
        script.async = true;
        script.onload = () => {
            window.botpressWebChat.init({
                botId,
                hostUrl: "https://cdn.botpress.cloud/webchat/v1",
                messagingUrl: "https://messaging.botpress.cloud",
                clientId: botId,
                userId,
                extraParams,
                containerId: "bp-web-widget",
            });
        };
        document.body.appendChild(script);
    }, [botId, userId, extraParams]);

    return <div id="bp-web-widget" style={{ width: "100%" }} />;
};

export default BotpressWebchat;
