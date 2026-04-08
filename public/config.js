const CONFIG = {
    SUPABASE_URL: "https://rsofsgxwqtpmuuzhoclu.supabase.co",
    SUPABASE_KEY: "sb_publishable_XVAQ2V4vVX9JMcOOpBTcVw_icaVT9SA",
    // Use localhost during development, update to Render URL when live
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? "http://localhost:5000" 
        : "https://final-year-project-kb04.onrender.com" 
};
