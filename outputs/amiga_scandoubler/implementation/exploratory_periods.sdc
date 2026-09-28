# Exploratory period-only checks on post-input-buffer nets.
# Port constraints were not propagated across the Gowin input buffers in the
# initial trial. These internal net names exist in board_1816/2048.json.
# This is NOT a model of the ADC/video phase relationship or board IO delays.
create_clock -name REF_27M -period 37.037037 [get_nets logic_core.clk_ref]
create_clock -name ADC_CLK -period 35.242291 [get_nets clocks.adc_clock]
create_clock -name VIDEO_CLK -period 17.621145 [get_nets video_clock]
