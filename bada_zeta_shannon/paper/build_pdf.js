#!/usr/bin/env node
/* bada_chatgpt_paper.html を A4 の PDF に組版する (Chromium / Playwright)。 */
const path = require("path");
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + path.join(__dirname, "bada_chatgpt_paper.html"));
  await page.pdf({
    path: path.join(__dirname, "bada_chatgpt_paper.pdf"),
    format: "A4",
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate: '<div style="width:100%;text-align:center;font-size:8pt;color:#555;font-family:IPAPGothic,IPAGothic,sans-serif"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
    margin: { top: "22mm", bottom: "20mm", left: "20mm", right: "20mm" },
  });
  await browser.close();
})();
