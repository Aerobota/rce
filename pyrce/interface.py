#!/usr/bin/env python
# -*- coding: utf-8 -*-
#     
#     interface.py
#     
#     This file is part of the RoboEarth Cloud Engine pyrce client.
#     
#     This file was originally created for RoboEearth
#     http://www.roboearth.org/
#     
#     The research leading to these results has received funding from
#     the European Union Seventh Framework Programme FP7/2007-2013 under
#     grant agreement no248942 RoboEarth.
#     
#     Copyright 2012 RoboEarth
#     
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#     
#     http://www.apache.org/licenses/LICENSE-2.0
#     
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#     
#     \author/s: Dominique Hunziker 
#     
#     

# Python specific imports
from uuid import uuid4
from threading import Event, Lock

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# ROS specific imports; if available
try:
    import rospy
    import genpy.message
    HAS_ROS = True
except ImportError:
    HAS_ROS = False

# twisted specific imports
from twisted.internet.defer import Deferred


class _Publisher(object):
    """ Abstract implementation of a Publisher Interface.
    """
    def __init__(self, conn, iTag, msgType):
        """ Initialize the Publisher.
        """
        self._conn = conn
        self._iTag = iTag
        self._msgType = msgType
    
    def publish(self, msg):
        """ Publish a message.
        """
        self._conn.sendMessage(self._iTag, self._msgType, msg, 'nil')


class _Subscriber(object):
    """ Abstract implementation of a Subscriber Interface.
    """
    def __init__(self, conn, iTag, msgType, cb):
        """ Initialize the Subscriber.
        """
        self._conn = conn
        self._iTag = iTag
        self._msgType = msgType
        self._cb = cb
    
    def unsubscribe(self):
        """ Unsubscribe from Interface. Afterwards no more messages are given
            to the registered callback.
        """
        self._conn.unregisterInterface(self._iTag, self)
    
    def callback(self, msgType, msg, _):
        """ Callback for Connection.
        """
        if not msgType == self._msgType:
            raise TypeError('Received unexpected message type.')
        
        self._cb(msg)
    
    def __del__(self):
        """ Finalize the Subscriber.
        """
        self.unsubscribe()


class _Service(object):
    """ Abstract implementation of a Service Interface.
    """
    def __init__(self, conn, iTag, srvType):
        """ Initialize the Service.
        """
        self._conn = conn
        self._iTag = iTag
        self._srvType = srvType
        
        self._responses = {}
    
    def callback(self, msgType, msg, msgID):
        """ Callback for Connection.
        """
        if not msgType == self._msgType:
            raise TypeError('Received unexpected message type.')
        
        deferred = self._responses.pop(msgID, None)
        
        if deferred:
            deferred.callback(msg)
    
    def __del__(self):
        """ Finalize the Service.
        """
        self._conn.unregisterInterface(self._iTag, self)


class Publisher(_Publisher):
    """ Representation of a Publisher Interface.
    """


class Subscriber(_Subscriber):
    """ Representation of a Subscriber Interface.
    """


class Service(_Service):
    """ Representation of a Service Interface.
    """
    def __init__(self, conn, iTag, srvType, cb):
        """ Initialize the Service.
        """
        super(Service, self).__init__(conn, iTag, srvType)
        
        self._cb = cb
    
    def call(self, msg, cb=None):
        """ Call the Service.
            
            @param msg:     Request message which should be sent.
            @type  msg:     JSON compatible dictionary.
            
            @param cb:      Callback function which will be called with the
                            response message as argument. If parameter is
                            omitted the default callback is tried as fall-back.
            @type  cb:      Callable / None
        """
        if not cb:
            cb = self._cb
        
        if not callable(cb):
            raise TypeError('Callback has to be callable.')
        
        uid = uuid4().hex
        deferred = Deferred()
        deferred.addCallback(cb)
        self._responses[uid] = deferred
        
        self._conn.sendMessage(self._iTag, self._srvType, msg, uid)


if HAS_ROS:
    class ROSPublisher(_Publisher):
        """ Representation of a Publisher Interface using ROS.
        """
        def __init__(self, conn, iTag, msgType, addr):
            """ Initialize the Publisher.
            """
            super(ROSPublisher, self).__init__(conn, iTag, msgType)
            
            self._sub = rospy.Subscriber(addr, rospy.AnyMsg, self._rosCB)
        
        def _rosCB(self, msg):
            """ Internally used callback for ROS Subscriber.
            """
            self.publish(StringIO(msg._buff))
        
        def __del__(self):
            """ Finalize the Publisher.
            """
            self._sub.unregister()
    
    
    class ROSSubscriber(_Subscriber):
        """ Representation of a Subscriber Interface using ROS.
        """
        def __init__(self, conn, iTag, msgType, addr):
            """ Initialize the Subscriber.
            """
            super().__init__(conn, iTag, msgType, self._callback)
            
            args = msgType.split('/')
        
            if len(args) != 2:
                raise ValueError('Message type is not valid. Has to be of the '
                                 'form pkg/msg, i.e. std_msgs/Int8.')
            
            msgCls = conn.loader.loadMsg(*args)
            
            self._pub = rospy.Publisher(addr, msgCls)
        
        def _callback(self, msg):
            """ Internally used method to send received messages to the ROS
                Publisher.
            """
            rosMsg = rospy.AnyMsg()
            rosMsg._buff = msg
            
            self._pub.publish(rosMsg)
        
        def __del__(self):
            """ Finalize the Subscriber.
            """
            self.unsubscribe()  # Is equal to super(_, self).__del__()
            self._pub.unregister()
    
    
    class ROSService(_Service):
        """ Representation of a Service Interface using ROS.
        """
        def __init__(self, conn, iTag, srvType, addr):
            """ Initialize the Service.
            """
            super(ROSService, self).__init__(conn, iTag, srvType, None)
            
            args = srvType.split('/')
            
            if len(args) != 2:
                raise ValueError('Invalid service type "{0}".'.format(srvType))
            
            
            if len(args) != 2:
                raise ValueError('Service type is not valid. Has to be of the '
                                 'form pkg/srv, i.e. std_msgs/Int8.')
        
            srvCls = conn.loader.loadSrv(*args)
            srvCls._request_class = rospy.AnyMsg
            srvCls._response_class = rospy.AnyMsg
            
            self._service = rospy.Service(addr, srvCls, self._rosCB)
            self._pendingLock = Lock()
            self._pending = {}
        
        def _rosCB(self, req):
            """ Internally used callback for ROS Service.
            """
            event = Event()
            
            uid = uuid4().hex
            deferred = Deferred()
            deferred.addCallback(self._callback, uid, event)
            self._responses[uid] = deferred
            
            self._conn.sendMessage(self._iTag, self._srvType,
                                   StringIO(req._buff), uid)
            event.wait()
            
            with self._pendingLock:
                response = self._pending.pop(uid, None)
            
            if not isinstance(response, genpy.message.Message):
                raise Exception('Interrupted.') # TODO: Change exception?
            
            return response
        
        def _callback(self, msg, uid, event):
            """ Internally used method to send received message to the ROS
                Service as response.
            """
            rosMsg = rospy.AnyMsg()
            rosMsg._buff = msg
            
            with self._pendingLock:
                self._pending[uid] = rosMsg
            
            event.set()
        
        def __del__(self):
            """ Finalize the Service.
            """
            super(ROSService, self).__del__()
            self._service.shutdown()
            
            with self._pendingLock:
                for event in self._pending.itervalues():
                    event.set()
                
                self._pending = {}