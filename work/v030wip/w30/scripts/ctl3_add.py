import sys;sys.path.insert(0,__import__("os").path.join(__import__("os").path.dirname(__file__),"../tools"))
import pcbnew as p;from pcbk7 import *
b=p.LoadBoard(sys.argv[1])
# 1) ADC_CLK: end the B.Cu corridor at a via just west of U2.63 (frees F.Cu under pins 60/61)
path(b,'ADC_CLK',[(41.45,44.4),(43.35,44.4),(43.95,45.0)],'B.Cu');via(b,'ADC_CLK',(43.95,45.0));path(b,'ADC_CLK',[(43.95,45.0),(45.05,45.0)])
# 2) U2.64 3V3: drop the F.Cu run to C38 (C38 keeps its own plane via) and use an inner via to In2
path(b,'3V3',[(45.05,45.4),(45.8,45.4),(46.04,45.2)]);via(b,'3V3',(46.04,45.2))
# 3) U2.65 GND: shorter stub into the EP corner (clears the new 3V3 inner via)
path(b,'GND',[(45.05,45.8),(46.4,45.8),(46.8,45.4)])
# 4) U2 left escapes + front vias (SDA/SCL/RESET/PWDN)
for net,pts in [('I2C_SDA',[(45.05,42.6),(44.05,42.6)]),('I2C_SCL',[(45.05,43.4),(43.55,43.4),(43.3,43.15)]),('ADC_RESET_N',[(45.05,43.8),(42.85,43.8),(42.55,43.5)]),('ADC_PWDN',[(45.05,44.2),(42.4,44.2),(41.8,43.6)])]:
    path(b,net,pts);via(b,net,pts[-1])
# 5) U1 escapes into the pad-ring interior + vias
for net,pts in [('I2C_SDA',[(33.65,36.0),(31.85,36.0),(31.6,36.25)]),('I2C_SCL',[(33.65,36.5),(32.6,36.5),(32.3,36.8),(32.3,36.95)]),('ADC_RESET_N',[(33.65,38.0),(32.65,38.0),(32.45,37.8)]),('ADC_PWDN',[(33.65,38.5),(32.5,38.5),(32.45,38.55)])]:
    path(b,net,pts);via(b,net,pts[-1])
finish(b,sys.argv[2])
