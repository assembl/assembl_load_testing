#!/usr/bin/env python3
import asyncio
import argparse
import pdb

from molotov import scenario, global_setup, setup_session
import simplejson as json


_SERVER = None
_HARS = []
_USER = None
_PASSWORD = None


def is_write(request):
    if request['method'] in ('GET', 'OPTIONS', 'HEAD'):
        return False
    if request['method'] != 'POST':
        return True
    if not request['url'].endswith('/graphql'):
        return True
    data = json.loads(request['postData']['text'])
    query = data['query']
    return 'mutation' in query


def as_dict(headers, lower=False):
    def maybe_lower(h):
        return h.lower() if lower else h
    return dict(zip([maybe_lower(x['name']) for x in headers],
                    [x['value'] for x in headers]))


@scenario(weight=100)
async def from_har(session):
    global _SERVER
    har = session.har
    requests = []
    responses = []
    for entry in har['log']['entries']:
        request, response = entry['request'], entry['response']
        if not request['url'].startswith(_SERVER):
            continue
        if response['status'] != 200:
            continue
        resp_headers = as_dict(response['headers'], True)
        if 'cache-control' in resp_headers:
            # skip cached entries
            continue
        postDatum = request.get('postData', (None))
        if postDatum:
            postDatum = postDatum['text']
        if responses and is_write(request):
            # make it sequential
            # print("waiting before", request)
            await asyncio.wait(
                responses, return_when=asyncio.FIRST_EXCEPTION)
        response = session.request(
            method=request['method'],
            url=request['url'],
            params=as_dict(request['queryString']),  # assuming no multi-value
            data=postDatum,
            headers=as_dict(request['headers']),
            verify_ssl=False,
            # TODO: cookies
        )
        requests.append(request)
        responses.append(response)
    assert responses, "No request found"
    done, pending = await asyncio.wait(
        responses, return_when=asyncio.FIRST_EXCEPTION)
    for task in done:
        resp = await task
        request = requests[responses.index(task._coro)]
        print(resp.status, request['url'])
        print()
        if resp.status != 200:
            print(resp.status, request)
            # pdb.set_trace()
        assert resp.status == 200


@setup_session()
async def do_login(worker_id, session):
    global _USER
    global _PASSWORD
    global _SERVER
    global _HARS
    session.har = _HARS[worker_id % len(_HARS)]
    resp = await session.post(_SERVER+'/legacy/login', data={
        'referrer': 'v2',
        'identifier': _USER,
        'password': _PASSWORD
    })
    if resp.status != 200:
        print("Could not login:", resp)
        # pdb.set_trace()
        assert False, 'could not login, check credentials'


def config(user=None, password=None, server=None, har_files=None):
    global _USER
    global _PASSWORD
    global _SERVER
    global _HARS
    if not (user and password and server and har_files):
        from configparser import ConfigParser
        parser = ConfigParser()
        with open('molotov.ini') as f:
            parser.read_file(f)
        _USER = user or parser.get('molotov', 'user')
        _PASSWORD = password or parser.get('molotov', 'password')
        _SERVER = server or parser.get('molotov', 'server')
        har_files = har_files or parser.get('molotov', 'har_files')
        assert _USER and _PASSWORD and _SERVER and har_files
    else:
        (_USER, _PASSWORD, _SERVER) = (user, password, server)
    for filename in har_files.split():
        with open(filename) as f:
            har = json.load(f)
            _HARS.append(har)


@global_setup()
def molotov_config(*args):
    # global _HARS
    config()
    # weight = 100/len(_HARS)
    # for har in _HARS:
    #     async def test(session):
    #         await from_har(session, har)
    #     scenario(weight=weight)(test)


async def main():
    import aiohttp
    async with aiohttp.ClientSession() as client:
        await do_login(0, client)
        await from_har(client)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("configuration", help="configuration file")
    parser.add_argument("-u", "--username")
    parser.add_argument("-p", "--password")
    parser.add_argument("-s", "--server")
    parser.add_argument('har', nargs='*', help='har files')
    args = parser.parse_args()
    config(args.username, args.password, args.server, args.har)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
