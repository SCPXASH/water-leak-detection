const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({headless: 'new'});
    const page = await browser.newPage();
    await page.goto('http://localhost:5000/dashboard');
    await new Promise(r => setTimeout(r, 4000));
    await page.screenshot({path: 'dashboard_screenshot.png', fullPage: true});
    await browser.close();
})();
