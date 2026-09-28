import sys;sys.path.insert(0,__import__("os").path.join(__import__("os").path.dirname(__file__),"../tools"))
import pcbnew as p;from pcbk7 import *
b=p.LoadBoard(sys.argv[1])
# B.Cu: U1 inner vias -> gaps in the x=35 via column -> 45deg parallel run -> U2 front vias
path(b,'ADC_PWDN',[(32.45,38.55),(32.65,38.75),(36.95,38.75),(41.8,43.6)],'B.Cu')
path(b,'ADC_RESET_N',[(32.45,37.8),(32.75,37.8),(33.35,38.4),(37.45,38.4),(42.55,43.5)],'B.Cu')
path(b,'I2C_SCL',[(32.3,36.95),(32.51,37.16),(37.31,37.16),(43.3,43.15)],'B.Cu')
path(b,'I2C_SDA',[(31.6,36.25),(34.1,36.25),(34.4,36.55)],'B.Cu')
path(b,'I2C_SDA',[(34.4,36.55),(34.65,36.8),(35.7,36.8)],'B.Cu',w=0.127)   # necked past GND via (35,36.225)
path(b,'I2C_SDA',[(35.7,36.8),(38.25,36.8),(44.05,42.6)],'B.Cu')
finish(b,sys.argv[2])
