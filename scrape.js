const axios = require("axios");
const cheerio = require("cheerio");

async function testScrape() {
  const archiveUrl = "http://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_draw_list_en.html";
  const { data } = await axios.get(archiveUrl, {
    headers: { "User-Agent": "Mozilla/5.0" },
  });
  const $ = cheerio.load(data);

  // List all querystrings in options
  $("select option").each((i, el) => {
    console.log($(el).attr("querystring"));
  });
}

testScrape();
