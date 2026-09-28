import sys;sys.path.insert(0,'/home/claude/tools')
import pcbedit as E
b=E.Board(sys.argv[1])
for net,pts in [('I2C_SDA',[(33.65,36.0),(32.4,36.0),(32.2,36.2)]),('I2C_SCL',[(33.65,36.5),(32.6,36.5),(32.3,36.8),(32.3,36.95)]),('ADC_RESET_N',[(33.65,38.0),(32.65,38.0),(32.45,37.8)]),('ADC_PWDN',[(33.65,38.5),(32.5,38.5),(32.45,38.55)])]:
    b.add_path(net,pts);b.add_via(net,pts[-1])
b.save(sys.argv[2])
