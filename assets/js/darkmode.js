document.addEventListener('DOMContentLoaded', (event) => {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        DarkReader.enable({
            brightness: 100,
            contrast: 100,
            sepia: 0,
            scheme: 'dark'
        });
        DarkReader.setFetchMethod(window.fetch);
        DarkReader.setDarkSchemeBackgroundColor('#000000');
    }else{
        DarkReader.disable()
    }
});
