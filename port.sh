#!/bin/bash

socat -v PTY,link=`pwd`/ttySCRIPT PTY,link=`pwd`/ttyMINICOM

