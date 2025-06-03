const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

async function fetch4D() {
  try {
    const url = "https://www.singaporepools.com.sg/en/product/4d";
    const { data } = await axios.get(url, {
      headers: { "User-Agent": "Mozilla/5.0" },
    });

    const $ = cheerio.load(data);
    const result = {
      date: $(".drawDate").first().text().trim(),
      firstPrize: $("#drawList .fourDResult .result1 span").text().trim(),
      secondPrize: $("#drawList .fourDResult .result2 span").text().trim(),
      thirdPrize: $("#drawList .fourDResult .result3 span").text().trim(),
      starterPrizes: [],
      consolationPrizes: [],
      updatedAt: new Date().toISOString(),
    };

    $("#drawList .fourDStarter span").each((_, el) =>
      result.starterPrizes.push($(el).text().trim())
    );
    $("#drawList .fourDConsolation span").each((_, el) =>
      result.consolationPrizes.push($(el).text().trim())
    );

    fs.writeFileSync("4d.json", JSON.stringify(result, null, 2));
    console.log("✅ 4D results scraped and saved.");
  } catch (err) {
    console.error("❌ Scraping failed:", err.message);
  }
}

fetch4D();
