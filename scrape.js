const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

async function fetch4D() {
  try {
    const url = "https://www.singaporepools.com.sg/en/product/Pages/4d_results.aspx";
    const { data } = await axios.get(url, {
      headers: { "User-Agent": "Mozilla/5.0" },
    });

    const $ = cheerio.load(data);

    // Array to store all draws
    const results = [];

    // Process each draw in the slider
    $(".divLatestDraws .slide-container li").each((index, element) => {
      const draw = $(element);
      
      const drawInfo = {
        date: draw.find(".drawDate").text().trim(),
        drawNumber: draw.find(".drawNumber").text().trim().replace("Draw No. ", ""),
        firstPrize: draw.find(".tdFirstPrize").text().trim(),
        secondPrize: draw.find(".tdSecondPrize").text().trim(),
        thirdPrize: draw.find(".tdThirdPrize").text().trim(),
        starterPrizes: [],
        consolationPrizes: []
      };

      // Extract starter prizes (2 columns per row)
      draw.find(".tbodyStarterPrizes tr").each((i, row) => {
        $(row).find("td").each((j, cell) => {
          const prize = $(cell).text().trim();
          if (prize) {
            drawInfo.starterPrizes.push(prize);
          }
        });
      });

      // Extract consolation prizes (2 columns per row)
      draw.find(".tbodyConsolationPrizes tr").each((i, row) => {
        $(row).find("td").each((j, cell) => {
          const prize = $(cell).text().trim();
          if (prize) {
            drawInfo.consolationPrizes.push(prize);
          }
        });
      });

      results.push(drawInfo);
    });

    const output = {
      scrapedAt: new Date().toISOString(),
      draws: results
    };

    fs.writeFileSync("4d.json", JSON.stringify(output, null, 2));
    console.log(`✅ Successfully scraped ${results.length} 4D draw(s) and saved to 4d.json`);
  } catch (err) {
    console.error("❌ Scraping failed:", err.message);
    process.exit(1);
  }
}

fetch4D();
