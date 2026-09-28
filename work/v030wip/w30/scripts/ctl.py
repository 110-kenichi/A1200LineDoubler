import sys;sys.path.insert(0,'/home/claude/tools')
import pcbedit as E
b=E.Board(sys.argv[1])
for net,pts in [('I2C_SDA',[(45.05,42.6),(44.05,42.6)]),('I2C_SCL',[(45.05,43.4),(43.55,43.4),(43.3,43.15)]),('ADC_RESET_N',[(45.05,43.8),(42.85,43.8),(42.55,43.5)]),('ADC_PWDN',[(45.05,44.2),(42.4,44.2),(41.8,43.6)])]:
    b.add_path(net,pts);b.add_via(net,pts[-1])
b.save(sys.argv[2])
