const puppeteer = require("puppeteer");
const fs = require("fs");

async function fetch4D() {
  const browser = await puppeteer.launch({ headless: "new" }); // or true for old versions
  const page = await browser.newPage();

  await page.goto("https://www.singaporepools.com.sg/en/product/pages/4d_results.aspx", {
    waitUntil: "networkidle2",
  });

  const result = await page.evaluate(() => {
    const getText = (selector) => {
      const el = document.querySelector(selector);
      return el ? el.innerText.trim() : "";
    };

    const getList = (selector) =>
      Array.from(document.querySelectorAll(selector)).map((el) => el.innerText.trim());

    return {
      date: getText(".drawDate"),
      firstPrize: getText(".result1 span"),
      secondPrize: getText(".result2 span"),
      thirdPrize: getText(".result3 span"),
      starterPrizes: getList(".fourDStarter span"),
      consolationPrizes: getList(".fourDConsolation span"),
      updatedAt: new Date().toISOString(),
    };
  });

  await browser.close();

  fs.writeFileSync("4d.json", JSON.stringify(result, null, 2));
  console.log("✅ 4D results saved to 4d.json");
}

fetch4D().catch((err) => {
  console.error("❌ Scraping failed:", err);
});
