#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       poseSubscriber.py
#       
#       This file is part of the RoboEarth Cloud Engine tests.
#       
#       This file was originally created for RoboEearth
#       http://www.roboearth.org/
#       
#       The research leading to these results has received funding from
#       the European Union Seventh Framework Programme FP7/2007-2013 under
#       grant agreement no248942 RoboEarth.
#       
#       Copyright 2012 RoboEarth
#       
#       Licensed under the Apache License, Version 2.0 (the "License");
#       you may not use this file except in compliance with the License.
#       You may obtain a copy of the License at
#       
#       http://www.apache.org/licenses/LICENSE-2.0
#       
#       Unless required by applicable law or agreed to in writing, software
#       distributed under the License is distributed on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#       See the License for the specific language governing permissions and
#       limitations under the License.
#       
#       \author/s: Gajamohan Mohanarajah 
#       
#       

import roslib; roslib.load_manifest('rceBinaryMsgDebug')
import rospy
from geometry_msgs.msg import Pose2D

def callback(data):
	print data

if __name__ == '__main__':
	rospy.init_node('ccPosSubscriber') #circle center position subscriber
	rospy.Subscriber('est_ccPos', Pose2D, callback)
	rospy.spin()
