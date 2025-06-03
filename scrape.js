const axios = require('axios');
const cheerio = require('cheerio');

async function scrapeLastRound() {
  const allResult = [];
  const startUrl = 'http://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_draw_list_en.html';

  const headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' +
                  '(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.5',
  };

  try {
    const webpageResp = await axios.get(startUrl, { headers });
    const $ = cheerio.load(webpageResp.data);

    // Find all <option> elements in the <select>
    const options = $('select option').toArray();

    if (options.length === 0) {
      console.error('No dates/options found in the select dropdown.');
      return allResult;
    }

    // Use the first option only (like your Python "break")
    const firstOption = options[0];
    const queryString = $(firstOption).attr('querystring');
    if (!queryString) {
      console.error('No querystring attribute found on first option.');
      return allResult;
    }

    const resultUrl = `http://www.singaporepools.com.sg/en/4d/Pages/Results.aspx?${queryString}`;
    const drawPageResp = await axios.get(resultUrl, { headers });

    const $$ = cheerio.load(drawPageResp.data);

    // Scrape first, second, third prizes
    const fPrize = $$('.tdFirstPrize').first().text().trim();
    const sPrize = $$('.tdSecondPrize').first().text().trim();
    const tPrize = $$('.tdThirdPrize').first().text().trim();

    allResult.push(fPrize, sPrize, tPrize);

    // Starter prizes
    $$('.tbodyStarterPrizes td').each((i, elem) => {
      allResult.push($$(elem).text().trim());
    });

    // Consolation prizes
    $$('.tbodyConsolationPrizes td').each((i, elem) => {
      allResult.push($$(elem).text().trim());
    });

    return allResult;

  } catch (error) {
    console.error('Error scraping 4D results:', error);
    return allResult;
  }
}

// Run and print results
scrapeLastRound().then(results => {
  console.log('4D Last Round Results:', results);
});
