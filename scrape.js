const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

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

    const options = $('select option').toArray();
    const firstOption = options[0];
    const queryString = $(firstOption).attr('querystring');

    const resultUrl = `http://www.singaporepools.com.sg/en/4d/Pages/Results.aspx?${queryString}`;
    const drawPageResp = await axios.get(resultUrl, { headers });

    const $$ = cheerio.load(drawPageResp.data);

    const fPrize = $$('.tdFirstPrize').first().text().trim();
    const sPrize = $$('.tdSecondPrize').first().text().trim();
    const tPrize = $$('.tdThirdPrize').first().text().trim();

    allResult.push(fPrize, sPrize, tPrize);

    $$('.tbodyStarterPrizes td').each((i, elem) => {
      allResult.push($$(elem).text().trim());
    });

    $$('.tbodyConsolationPrizes td').each((i, elem) => {
      allResult.push($$(elem).text().trim());
    });

    // Save to 4d.json
    fs.writeFileSync('4d.json', JSON.stringify(allResult, null, 2), 'utf-8');
    console.log('4d.json updated successfully');

    return allResult;

  } catch (error) {
    console.error('Error scraping 4D results:', error);
    return allResult;
  }
}

scrapeLastRound().then(results => {
  console.log('4D Last Round Results:', results);
});
