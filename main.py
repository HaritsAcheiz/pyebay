import scraper
import transform

if __name__ == '__main__':
    # target = 'https://www.ebay.com/itm/225625920147'
    target = 'https://www.ebay.com/itm/154683625039'
    s = scraper.EbayScraper()
    t = transform.TransformEbay()
    s.run(target)
    t.run()
