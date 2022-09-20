---
layout: post
title:  Firebase- Could not locate configuration file: 'GoogleService-Info.plist'"
author: sal
date: 2020-07-24-03:25:54
categories: [ Jekyll, tutorial ]
image: assets/images/4.jpg
---
### Firebase- Could not locate configuration file: 'GoogleService-Info.plist'
<p>I tried so many copy paste methods even creating/placing plist file in the Resource folder and nothing worked :(

sometimes, only using original plist file was best indicator of working but this is the best solution that worked 100% every time I use Xcode (8 - 9)/swift and Firebase together:

Go to your project settings
Press on Build Phases
Press on Copy Bundle Resources (to expand)
Drag the your GoogleServices-Info.plist into this folder
now Run the project and it should work :D</p>

##[Full Ref](https://stackoverflow.com/questions/38250528/firebase-could-not-locate-configuration-file-googleservice-info-plist)