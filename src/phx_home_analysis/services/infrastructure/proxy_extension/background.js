// Template file for proxy authentication extension
// Placeholders will be replaced with actual credentials at runtime

const config = {
    host: "PROXY_HOST",
    port: PROXY_PORT,
    username: "PROXY_USERNAME",
    password: "PROXY_PASSWORD"
};

// Configure proxy settings
chrome.proxy.settings.set({
    value: {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: config.host,
                port: config.port
            },
            bypassList: ["localhost", "127.0.0.1"]
        }
    },
    scope: "regular"
});

// Handle authentication requests
chrome.webRequest.onAuthRequired.addListener(
    function(details, callbackFn) {
        callbackFn({
            authCredentials: {
                username: config.username,
                password: config.password
            }
        });
    },
    {urls: ["<all_urls>"]},
    ["asyncBlocking"]
);

console.log("Proxy Auth Helper loaded - proxy configured for " + config.host + ":" + config.port);
