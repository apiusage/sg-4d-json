const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
  "Accept-Language": "en-US,en;q=0.5",
};

const archiveUrl = "http://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_draw_list_en.html";

async function scrapeDraws(numOfRounds = 5, scrapeAll = false) {
  try {
    const archiveResp = await axios.get(archiveUrl, { headers: HEADERS });
    const $archive = cheerio.load(archiveResp.data);

    // Extract all draw option querystrings
    const options = $("select option")
      .map((_, el) => $(el).attr("querystring"))
      .get();

    const maxRounds = scrapeAll ? options.length : Math.min(numOfRounds, options.length);
    const results = [];

    for (let i = 0; i < maxRounds; i++) {
      const url = "http://www.singaporepools.com.sg/en/4d/Pages/Results.aspx?" + options[i];
      console.log(`Scraping round ${i + 1}/${maxRounds}: ${url}`);

      const drawResp = await axios.get(url, { headers: HEADERS });
      const $ = cheerio.load(drawResp.data);

      // Extract prizes
      const firstPrize = $(".tdFirstPrize").first().text().trim();
      const secondPrize = $(".tdSecondPrize").first().text().trim();
      const thirdPrize = $(".tdThirdPrize").first().text().trim();

      // Extract starter prizes
      const starterPrizes = [];
      $("tbody.tbodyStarterPrizes td").each((_, el) => {
        starterPrizes.push($(el).text().trim());
      });

      // Extract consolation prizes
      const consolationPrizes = [];
      $("tbody.tbodyConsolationPrizes td").each((_, el) => {
        consolationPrizes.push($(el).text().trim());
      });

      results.push({
        drawDate: options[i], // you can replace with better date extraction if available
        firstPrize,
        secondPrize,
        thirdPrize,
        starterPrizes,
        consolationPrizes,
        scrapedAt: new Date().toISOString(),
      });

      // Simple progress update
      process.stdout.write(`Scraped ${i + 1} / ${maxRounds}\r`);
    }

    // Save results to file
    fs.writeFileSync("4d.json", JSON.stringify(results, null, 2));
    console.log("\n✅ Done scraping, saved to 4d.json");

  } catch (err) {
    console.error("❌ Error scraping:", err.message);
  }
}

scrapeDraws(5, false);
