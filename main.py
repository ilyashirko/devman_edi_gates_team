import xml.etree.ElementTree as ET
from datetime import datetime

from terminaltables import AsciiTable

FILES = ('RS_Via-3.xml', 'RS_ViaOW.xml')

KEY_TAGS = [
    "Source",
    "DepartureTimeStamp",
    "Destination",
    "ArrivalTimeStamp",
    "Class",
    "TicketType",
    "NumberOfStops"
]


def extract_flights_info(flights):
    flights_info = []
    for flight in flights:
        flight_info = {}
        for tag in KEY_TAGS:
            if tag in ("DepartureTimeStamp", "ArrivalTimeStamp"):
                flight_info.update(
                    {
                        tag: datetime.strptime(
                            flight.find(tag).text, '%Y-%m-%dT%H%M'
                        )
                    }
                )
            else:
                flight_info.update({tag: flight.find(tag).text})
        flights_info.append(flight_info)
    return flights_info


def extract_xml_response(xml_file):
    root_node = ET.parse(xml_file).getroot()

    routes = root_node.findall('PricedItineraries/Flights')
    extracted_info = []
    for route in routes:
        route_info = {}

        onward_flights = extract_flights_info(
            route.findall('OnwardPricedItinerary/Flights/Flight')
        )
        route_info.update({'onward_flights': onward_flights})

        return_flights = extract_flights_info(
            route.findall('ReturnPricedItinerary/Flights/Flight')
        )
        route_info.update({'return_flights': return_flights})

        currencies = route.findall('Pricing')
        payment = {}
        for currency in currencies:
            currency_info = {}
            prices = currency.findall('ServiceCharges')
            for price in prices:
                if (price.get("type") not in currency_info and
                        price.get('ChargeType') == 'TotalAmount'):
                    currency_info.update(
                        {
                            price.get('type'): [
                                price.text, currency.get('currency')
                            ]
                        }
                    )
            payment.update(currency_info)
        route_info.update({'payment': payment})
        extracted_info.append(route_info)
    return extracted_info


def get_summary_info(response):
    summary_info = {
        'route': [],
        'leaving_onward_from': None,
        'leaving_onward_to': [],
        'onward_class': [],
        'onward_ticket_type': [],
        'arriving_return_from': [],
        'arriving_return_to': [],
        'return_class': [],
        'return_ticket_type': []
    }

    for route in response:
        onward = route['onward_flights']
        # get route code name
        points = f"{onward[0]['Source']} - {onward[len(onward) - 1]['Destination']}"
        if points not in summary_info['route']:
            summary_info['route'].append(points)

        # get minimum living onward time
        if (not summary_info['leaving_onward_from'] or
                onward[0]['DepartureTimeStamp'] < summary_info['leaving_onward_from']):
            summary_info['leaving_onward_from'] = onward[0]['DepartureTimeStamp']

        # get maximun living onward time
        if (not summary_info['leaving_onward_to'] or
                onward[0]['DepartureTimeStamp'] > summary_info['leaving_onward_to']):
            summary_info['leaving_onward_to'] = onward[0]['DepartureTimeStamp']

        # get all available flight classes
        if onward[0]['Class'] not in summary_info['onward_class']:
            summary_info['onward_class'].append(onward[0]['Class'])

        # get all available ticket types
        if onward[0]['TicketType'] not in summary_info['onward_ticket_type']:
            summary_info['onward_ticket_type'].append(onward[0]['TicketType'])

        # get the same return flights info if available
        if route['return_flights']:
            return_fl = route['return_flights']
            if (not summary_info['arriving_return_from'] or
                    return_fl[len(return_fl) - 1]['DepartureTimeStamp'] < summary_info['arriving_return_from']):
                summary_info['arriving_return_from'] = (
                    return_fl[len(return_fl) - 1]['DepartureTimeStamp']
                )

            if (not summary_info['arriving_return_to'] or
                    return_fl[len(return_fl) - 1]['DepartureTimeStamp'] > summary_info['arriving_return_to']):
                summary_info['arriving_return_to'] = (
                    return_fl[len(return_fl) - 1]['DepartureTimeStamp']
                )

            if return_fl[0]['Class'] not in summary_info['return_class']:
                summary_info['return_class'].append(return_fl[0]['Class'])

            if return_fl[0]['TicketType'] not in summary_info['return_ticket_type']:
                summary_info['return_ticket_type'].append(return_fl[0]['TicketType'])
    return summary_info


def make_summary_table(summary_info):
    table = [
        ['KEY PARAMETERS', 'VALUES']
    ]
    for key, value in summary_info.items():
        table.append([key, value])
    return table


if __name__ == '__main__':
    for file in FILES:
        response = extract_xml_response(file)
        summary_info = get_summary_info(response)
        print(AsciiTable(make_summary_table(summary_info), file).table)
