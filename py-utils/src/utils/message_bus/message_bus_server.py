#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import json
from aiohttp import web
from cortx.utils.utils_server import RestServer
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.utils_server.error import RestServerError
from cortx.utils.message_bus import MessageConsumer, MessageProducer

routes = web.RouteTableDef()


class MessageBusRequestHandler(RestServer):
    """ Rest interface of message bus """

    @staticmethod
    async def send(request):
        try:
            message_type = request.match_info['message_type']
            payload = await request.json()
            messages = payload['messages']
            producer = MessageProducer(producer_id='rest_producer', \
                message_type=message_type, method='sync')

            producer.send(messages)
        except MessageBusError as e:
            status_code = e.rc
            error_message = e.desc
            response_obj = {'error_code': status_code, 'exception': \
                ['MessageBusError', {'message': error_message}]}
        except Exception as e:
            exception_key = type(e).__name__
            exception = RestServerError(exception_key).http_error()
            status_code = exception[0]
            error_message = exception[1]
            response_obj = {'error_code': status_code, 'exception': \
                [exception_key, {'message': error_message}]}
            raise MessageBusError(status_code, error_message) from e
        else:
            status_code = 200  # No exception, Success
            response_obj = {'status_code': status_code, 'status': 'success'}
        finally:
            return web.Response(text=json.dumps(response_obj), \
                status=status_code)

    @staticmethod
    async def receive(request):
        try:
            message_types = str(request.match_info['message_type']).split('&')
            consumer_group = request.rel_url.query['consumer_group']
            consumer = MessageConsumer(consumer_id='rest_consumer', \
                consumer_group=consumer_group, message_types=message_types, \
                auto_ack=True, offset='latest')

            message = consumer.receive()
        except MessageBusError as e:
            status_code = e.rc
            error_message = e.desc
            response_obj = {'error_code': status_code, 'exception': \
                ['MessageBusError', {'message': error_message}]}
        except Exception as e:
            exception_key = type(e).__name__
            exception = RestServerError(exception_key).http_error()
            status_code = exception[0]
            error_message = exception[1]
            response_obj = {'error_code': status_code, 'exception': \
                [exception_key, {'message': error_message}]}
            raise MessageBusError(status_code, error_message) from e
        else:
            status_code = 200  # No exception, Success
            response_obj = {'messages': str(message)}
        finally:
            return web.Response(text=json.dumps(response_obj), \
                status=status_code)