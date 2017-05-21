import csv
import os

import bs4
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    base_url = 'https://www.s7.ru/info/faq/faq.dot'
    urls = [
        ('s7_priority',
         [
             'registration-1', 'profile', 'cards', 'association', 'miles', 'flight', 'partners', 'validity', 'bonus',
             'privileges', 'charity', 'bank-cards'
         ]),
        ('booking', [
            'ticket_online', 'hotel_online', 'car_online', 'transfer_taxi_aeroexpress', 's7_mobile', 'payment',
            'insurance_online', 'additional_baggage', 'additional_questions'
        ]),
        ('management_of_booking', ['booking_exchange', 'booking_modification', 'booking_return']),
        ('registration', ['online', 'mobile', 'reception', 'bronirovanie']),
        ('before_flight', ['special_passengers', 'children', 'animals']),
        ('baggage', ['rules', 'hand_luggage', 'dangerous', 'special_luggage', 'customs', 'animals-1', 'loss_return']),
        ('time_table-1', ['time_table', 'tariff', 'transfer', 'event-1', 'service_class', 'flying_envelopes']),
        ('airport', ['service', 'time_table-2', 'business_hall', 'waiting_room']),
        ('in_flight', ['meals', 'additional_questions-1']),
        ('company', ['general_questions', 'fleet']),
        ('important-information', ['important-level2'])
    ]

    with open(os.path.join(CURRENT_DIR, 'faq.csv'), 'w') as f:
        writer = csv.DictWriter(f, ['category', 'title', 'text'])

        i = 0
        for cat, subcats in urls:
            for subcat in subcats:
                resp = requests.get((base_url + '?cat={}&subCat={}').format(cat, subcat))
                page = resp.content
                parsed_page = bs4.BeautifulSoup(page)
                divs = parsed_page.find_all("div", {"class": "single_toggle"})
                for one_q in divs:
                    title_div = one_q.find("p", {"class": "toggler"})
                    answer_div = one_q.find("div", {"class": "toggle_content"})

                    title = title_div.text.strip()
                    answer = answer_div.text.strip()

                    writer.writerow({
                        'category': cat,
                        'title': title,
                        'text': answer
                    })

            i += 1
            print('Finished {}: {}/{}'.format(cat, i, len(urls)))


if __name__ == '__main__':
    main()
