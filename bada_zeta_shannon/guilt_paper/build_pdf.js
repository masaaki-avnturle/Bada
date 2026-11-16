#!/usr/bin/env node
/* guilt_gate_paper.html を A4 の PDF に組版する (Chromium / Playwright)。 */
const path = require("path");
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + path.join(__dirname, "guilt_gate_paper.html"));
  await page.pdf({
    path: path.join(__dirname, "guilt_gate_paper.pdf"),
    format: "A4",
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate: '<div style="width:100%;text-align:center;font-size:8pt;color:#555;font-family:DejaVu Sans,sans-serif"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
    margin: { top: "23mm", bottom: "21mm", left: "22mm", right: "22mm" },
  });
  await browser.close();
})();
