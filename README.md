# Quickly Start

## For pypi

We have package our repository into [simple-emulator](https://pypi.org/project/simple-emulator/),
which means that you can run order

> pip install simple-emulator

to install it.

There may be some differences between this and below. But you can finished according to the next steps :

- create your module

```python
from simple_emulator import BlockSelection, CongestionControl


# Your solution should include packet selection and congestion control.
# So, we recommend you to achieve it by inherit the objects we provided and overwritten necessary method.
class Solution(BlockSelection, CongestionControl):
    pass
```

- create emulator

```python
from simple_emulator import SimpleEmulator


# Use the object you created above
my_solution = Solution()
emulator = SimpleEmulator(solution=my_solution)
```

- run emualtor

```python
# You can specify the time for the emualtor's running.
# It will run until there is no packet can sent by default. 
emulator.run_for_dur()
```

Here is an complete  [demo](https://github.com/AItransCompetition/Meet-Deadline-Requirements/tree/master/solution_examples) about the using of pypi.

## For this repository

For players, you need to finish the code both of  "congestion_control_algorithm.py" 
and "block_selection.py" files in path of "/player".

Here we provide you some congestion control algorithm.
By default the congestion control is "reno" and block selection algorithm is selecting block which is closest to it's deadline.

Then, just run the order "python3 run_this.py".

You will get some output in the path "/output/" and should fix your code according to the output.

Here is an complete  [demo](https://github.com/AItransCompetition/Meet-Deadline-Requirements/blob/master/run_this.py) about the using of this repository.

# For Detail

## player

Here are the 3 methods that players need to finished.

### aitrans_solution.py

It should be implemented with these method :

- [select_block](#select_block)
- [on_packet_sent](#on_packet_sent)
- [cc_trigger](#cc_trigger)

In case you forget, we recommend you implement by inheriting the objects from Solution in block_selection.py and Solution in congestion_control_algorithm.py and overwrite these methods.

Here is the explanations of [Input](#Input) and [Output](#Output) .

### block_selection.py

In this module, you have to implement the function "select_block" with the parameters "cur_time, block_queue" and return an integer value which means the block index in block queue, which will be sent at the time "cur_time".

Here we provided a [example](https://github.com/AItransCompetition/simple_emulator/blob/mmgc/player/block_selection.py) of selecting block by the **create time** firstly, and **radio of rest life time to deadline** secondly.

#### select_block

For every block in block queue, it's implement in "objects/block.py". But we recommend you to get more information at  [Block](#block-log) .

### congestion_control_algorithm.py

In this module, you have to implement a class with member function "on_packet_sent" and "cc_trigger". So we recommend you to accomplish this by inheriting from the object of "CongestionControl" implemented in "cc_base.py" in case you forget these. 

Here we provided some simple algorithms about congestion control to help you being familiar with this competition.
Like [Reno](https://github.com/AItransCompetition/Meet-Deadline-Requirements/tree/master/solution_examples/reno) and an example about [reinforcement learning](https://github.com/AItransCompetition/Meet-Deadline-Requirements/tree/master/solution_examples/rl_torch) implemented by tensorflow.

#### on_packet_sent

For the member function "on_packet_sent", we will call it every time I want to send a packet. And it should return a dictionary with window size and send rate according to the information from "_input_list", just like below.

```json
{
    "cwnd" : 10,
    "send_rate" : 10
}
```

#### cc_trigger

For every item information in "_input_list",  it is a triad of **(event_time, event_type, and packet_information_dict)**. 

- event_time

  > The time when the packet arrived.

- event_type

  > We divide the packet into three categories : PACKET_TYPE_FINISHED, PACKET_TYPE_TEMP, PACKET_TYPE_DROP.
  >
  > PACKET_TYPE_FINISHED : The acknowledge packet that successfully reached the source point;
  >
  > PACKET_TYPE_TEMP : The packet that have not yet reached the source point;
  >
  > PACKET_TYPE_DROP : The packet used to inform the source point of packet loss.

- packet_information_dict

  > The packet it the object implemented in "objects/packet.py". But we recommend you to get more information at [Packet](#packet-log) .

Why we design a individual function to add element to "_input_list"?

It's because there are some congestion control algorithm that need to update window size and send rate immediately. So you need to return a dictionary with window size and send rate if you want to do some changes as soon as the data is received , like [here](#on_packet_sent).

## The calculation of score

We use this QOE function to calculate score of your solution :
$$
QOE = \sum_{block \in Blocks} \alpha*priority + \beta*Miss_ddl
$$
And here is [parameters' explanation](#Table-:-QOE_parameters).

## config

### constant

Here are some constants that may be help for you：

- USE_CWND

  > Set "False" if your congestion control algorithm don't use cwnd.

- ENABLE_LOG

  > Set "False" if you don't want to generate packet log in path "output/packet_log".

- MAX_PACKET_LOG_ROWS

  > The number of rows for a single packet log. If you just want to use one file to log, set it "None".

All of these constants can be set on the create of emulator by the key words arguments.

### Block data

We create the block by using the file "data_audio.csv" and "data_video.csv" which are record from WebRTC.

For "data_audio.csv", the first columns is the created time of block and the second columns is the block size. 

| Time (s) | Block Size (B) |
| -------- | -------------- |
| 0.0      | 514            |
| 0.06     | 305            |
| ...      | ...            |

For "data_video.csv", it has the same columns like "data_audio.csv" except the third columns, which means P frame or I frame.

| Time (s) | Block_size (B) | Frame Type |
| -------- | -------------- | ---------- |
| 0.0      | 9584           | P          |
| 0.033    | 8069           | P          |
| ...      | ...            | ...        |

### Trace data

We use the generated trace data by using the Hidden Markov algorithm to simulate the bandwidth changing of the network, which is implemented in "scripts/network.py". 

For the trace file, the first columns is the changed time of bandwidth. The second columns is the bandwidth whose unit is megabytes. And the third columns is the link random loss rate. Finally, the last columns is the fixed propagation delay of link whose unit is seconds.

| Time (s) | Bandwidth (MB)     | Loss Rate(%) | Propagation Delay (s) |
| -------- | ------------------ | ------------ | --------------------- |
| 0        | 19.38592070201254  | 0            | 0.001                 |
| 1        | 24.832955411664393 | 0            | 0.001                 |
| ...      | ...                | ...          | ...                   |

## objects

Here are all the objects that our system uses. You can get more details from our powerpoint presentation.

What I want to emphasize here is that, your congestion control module, which implemented in "player/congestion_control_algorithm.py", should inherit from the object of "CongestionControl" implemented in "cc_base.py". 

We've provided some examples of classic congestion control algorithms in path "player/examples", like [Reno](https://en.wikipedia.org/wiki/TCP_congestion_control).

## output

### packet log

We will output all the packet log into the directory. Here you can get one packet all life time.

Because of there may be so many packet information that logging file is big. So we split all information into different files if its rows exceed **MAX_PACKET_LOG_ROWS** which you can reset in "config/constant.py".

For every row,  it's form like below：

```json
{
    "Time": 0.0, 
    "Waiting_for_ack_nums": 0, 
    "Sender_id": 1, 
    "Type": "S", 
    "Position": 0, 
    "Send_delay": 0.0, 
    "Pacing_delay": 0.0, 
    "Latency": 0.0, 
    "Drop": 0, 
    "Packet_id": 1, 
    "Create_time": 0.0, 
    "Offset": 0, 
    "Payload": 1480, 
    "Packet_size": 1500, 
    "Extra": {
        "Cwnd": 1
    }, 
    "Block_info": {
        "Block_id": 1, 
        "Priority": "0", 
        "Deadline": 0.2, 
        "Create_time": 0.0, 
        "Size": 200000.0
    }
}
```

Here is every key's explanation：

- Time : The time handle this event;
- Waiting_for_ack_nums : The numbers of packets that sended but not acknowledged by source.
- Sender_id : The sender's id that sent this packet;
- Type : To distinguish sending or acknowledge packet;
- Position : The position that packet on. It's 0 if packet on source'
- Send_delay : The time that packet sent into window;
- Pacing_delay : The time that packet send into network. It's used in the congestion control like BBR.
- Latency : The time that packet spending on links including queue delay and propagation delay;
- Drop : Label whether the packet is dropped;
- Packet_id : The Identity of packet;
- Create_time : The time when the packet is created;
- Offset : The offset of the packet in its block;
- Payload : The size of valid data in packet whose unit is bytes;
- Packet_size : The size of the packet whose unit is bytes;
- Extra : The filed we provided for your congestion control. 
We will fill it when system need to send packet (equals to calling "on_packet_sent" method in your solution).
    - Cwnd : The size of crowded window at sender.Its unit is packet; 
- Block_info : The block information that the packet belong to. You can get more from below.

### block log

Here is all of the blocks that the system sent.

For every row, it's form like below：

``` json
{
    "Block_id": 4, 
    "Priority": "0", 
    "Deadline": 0.2, 
    "Create_time": 3.0, 
    "Size": 200000.0, 
    "Send_delay": 0.0, 
    "Latency": 1.4900000000000104, 
    "Finish_timestamp": 3.0425, 
    "Miss_ddl": 0, 
    "Split_nums": 136, 
    "Finished_bytes": 200000.0
}
```

Here is every key's explanation：

- Priority : The degree of emergency of block;
- Block_id : The identity of block;
- Size : The size of block whose unit is bytes;
- Deadline : The block's failure time size;
- Create_time : The time when block is created;
- Send_delay : The sum of all packets's "send_delay" which belong to the block;
- Latency : The sum of all packets's "latency" which belong to the block;
- Finish_timestamp :  The time when block is finished if it don't miss deadine; Otherwise, it's the time when the block was detected failure;
- Miss_ddl : Whether the block is miss deadline;
- Split_nums : The count of packets that the block is divided;
- Finished_bytes : The number of bytes received by the receiver.

### cwnd_changing.png

Here we provided a simple schematic diagram of window change process according to partial packet log.

The horizontal axis is the time(seconds), the left vertical axis is the number of packets, and the right vertical axis is the bandwidth (unit is packet).So solid lines represent window changes and dashed lines represent bandwidth changes.

We put the draw function in the "plot_cwnd" of "utils.py". You can specify the value of "raws" to set the amount of data to be processed, specify the value of "time_range" to set the the time interval you want see, and  specify the value of "scatter" to use a line chart or scatter chart.

![cwnd_changing](output/cwnd_changing.png)

### emulator-analysis.png

Here we provided a simple schematic diagram of latency of packets change process according to partial packet log.

The horizontal axis is the time(seconds), the left vertical axis is the latency of packets. So solid lines represent latency changes. And the cross indicates that the packet was lost at this time.

We put the draw function in the "analyze_emulator" of "utils.py". You also can describe these parameters mentioned above and do some customization, like "rows", "time_range" and "scatter".

![emulator-analysis](output/emulator-analysis.png)

### throughput_changing.png

![throughput_changing](output/throughput_changing.png)

# Appendix

## Input

|  Variable   |                         Explanation                          |                      Sample                       |
| :---------: | :----------------------------------------------------------: | :-----------------------------------------------: |
|  cur_time   |                       current time(s)                        |                     0.0（s）                      |
| block_queue | The block queue currently to be sent at the sender, the field information of each packet is shown in the table [packet_queue](#Table-:-block_queue) |               [packet_1, packet_2]                |
|    data     | For the ACK or Lost information returned by the receiving end, the field information of each packet is shown in the table [data](#Table-:-data) | [event_time, event_type, packet_information_dict] |

## Output

|  Variable   |                         Explanation                          |    Sample     |
| :---------: | :----------------------------------------------------------: | :-----------: |
| block_index | The index value of the block to be sent at the current moment in block_queue |    1(int)     |
|    Cwnd     |       The current congestion window size of the sender       | 10（packet）  |
|  Send_rate  |     The sending rate of the sender at the current moment     | 5（packet/s） |

## Table : block_queue

|  Variable   |                         Explanation                          |    Sample     |
| :---------: | :----------------------------------------------------------: | :-----------: |
| packet_type | Packet type, divided into two types,'S' and'A', which respectively represent the sending process and the confirming process |   A（str）    |
| create_time |             The time when the packet was created             |   0.1（s）    |
|   offset    |  The offset of the packet in the block to which it belongs   |   1（int）    |
|  packet_id  |              ID of the packet, globally unique               |   1（int）    |
|   payload   | The actual effective data size of the packet in block（Bytes） | 1480（Bytes） |
| packet_size |             The actual size of the packet(Bytes)             | 1500（Bytes） |
| block_info  | The information of the block to which the packet belongs, the type is dict, and the field information contained in it is shown in the table [block_info](#Table-:-block_info) |   0.0（s）    |

## Table : block_info

|  Variable   |                      Explanation                      |     Sample      |
| :---------: | :---------------------------------------------------: | :-------------: |
|  Block_id   |               Block ID, globally unique               |    1（int）     |
|  Priority   | The priority of the block, the values are 0, 1, and 2 |    1（int）     |
|  Deadline   |              Block expiration time size               |    0.2（s）     |
| Create_time |          The time when the block was created          |    0.1（s）     |
|    Size     |                   Block size(Bytes)                   | 200000（Bytes） |

## Table : data

|        Variable         |                         Explanation                          |  Sample  |
| :---------------------: | :----------------------------------------------------------: | :------: |
|       event_time        |                       Current time(s)                        | 0.1（s） |
|       event_type        | The event type of the packet, the values can be F, D, and T, which represent completed packets, dropped packets, and intermediate state packets (that is, packets other than the first two types) | F（str） |
| packet_information_dict | A dictionary composed of the brief information of the packet, the field information of each packet is shown in the table [packet_information_dict](#Table-:-packet_information_dict) |          |

## Table : packet_information_dict

|    Variable    |                             Explanation                             |     Sample     |
| :----------: | :----------------------------------------------------------: | :----------: |
|     Type     |      Packet type, divided into two types,'S' and'A', which respectively represent the sending process and the confirming process      |   S（str）   |
|   Position   | The location of the packet, when it is at the sending end, it is 0 |   0（int）   |
|  Send_delay  |                           Send delay                           |   0.1（s）   |
|   Latency   | The delay spent by the packet on the link, including the queuing delay of all hops that have passed and the propagation delay of the link |   0.2（s）   |
|     Drop     |                Whether the packet is a packet indicating discarded information                |   0（int)    |
|  Packet_id   |                      ID of the packet, globally unique                      |  100（int）  |
| Create_time  |                        The time when the packet was created                        |   0.0（s）   |
|    Offset    | The offset of the packet in the block to which it belongs |   0（int）   |
|   Payload    |              The actual effective data size of the packet in block(Bytes)              | 1480（Byte） |
| Packet_size  |             The actual size of the packet(Bytes) | 1500（Byte） |
|  Block_info  | The information of the block to which the packet belongs, the type is dict, and the field information contained in it is shown in the table [block_info](#Table-:-block_info) |              |
|    Extra     | Additional information. This field provides players with customized information. Each time a packet is sent, the "on_packet_sent" function in the player module will be called to obtain the latest Extra field information returned by it. Fill in the packet, which may contain See the table for field information [Extra](Table-:-Extra) |              |

## Table : Extra

| Variable |                             Explanation                             |    Sample |
| :-------: | :----------------------------------------------------------: | :-----------: |
|   Cwnd    | The size of the congestion window of the sender at the current moment, the unit is a packet, which is valid only when the congestion window is used |  5 (packet)   |
| Send_rate | The sending rate of the sender at the current moment, the unit is packet/s, currently only valid when the player uses the rate-based congestion algorithm | 10 (packet/s) |
| inflight | The number of packets that have been sent by the sender but have not received ack or lost information at the current moment | 10 (packet) |

## Table : QOE_parameters

| Variable |                      Explanation                      | Sample  |
| :------: | :---------------------------------------------------: | :-----: |
| Priority | The priority of the block, the values are 0, 1, and 2 | 0 (int) |
| Miss_ddl |            whether the block miss deadline            | 1 (int) |

