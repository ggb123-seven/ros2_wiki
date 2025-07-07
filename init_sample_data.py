#!/usr/bin/env python3
import sqlite3
from werkzeug.security import generate_password_hash

def init_sample_data():
    conn = sqlite3.connect('ros2_wiki.db')
    cursor = conn.cursor()
    
    # 创建管理员用户
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash) 
        VALUES ('admin', 'admin@ros2wiki.com', ?)
    ''', (admin_password,))
    
    # 创建示例用户
    user_password = generate_password_hash('user123')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash) 
        VALUES ('ros2_learner', 'learner@example.com', ?)
    ''', (user_password,))
    
    # 获取管理员用户ID
    cursor.execute('SELECT id FROM users WHERE username = "admin"')
    admin_id = cursor.fetchone()[0]
    
    # 创建示例文档
    sample_documents = [
        {
            'title': 'ROS2快速入门指南',
            'content': '''# ROS2快速入门指南

## 什么是ROS2？

ROS2（Robot Operating System 2）是一个开源的机器人操作系统，提供了一套工具、库和约定，用于简化复杂和健壮的机器人行为的创建。

## 核心概念

### 1. 节点（Node）
节点是ROS2中最基本的执行单元，每个节点都是一个独立的进程。

```python
import rclpy
from rclpy.node import Node

class MinimalNode(Node):
    def __init__(self):
        super().__init__('minimal_node')
        self.get_logger().info('Hello ROS2!')

def main(args=None):
    rclpy.init(args=args)
    node = MinimalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 2. 话题（Topic）
话题是节点之间进行异步通信的方式。

```python
# 发布者
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class Publisher(Node):
    def __init__(self):
        super().__init__('publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello World: {self.i}'
        self.publisher_.publish(msg)
        self.i += 1
```

## 安装ROS2

### Ubuntu系统安装

```bash
# 添加ROS2仓库
sudo apt update && sudo apt install curl gnupg2 lsb-release
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64,arm64] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'

# 安装ROS2
sudo apt update
sudo apt install ros-humble-desktop
```

### 环境配置

```bash
# 添加到.bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## 创建工作空间

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
source install/setup.bash
```

这就是ROS2的基础入门内容，接下来我们将深入学习更多高级特性。
''',
            'category': 'ROS2基础',
            'author_id': admin_id
        },
        {
            'title': 'ROS2服务通信详解',
            'content': '''# ROS2服务通信详解

## 服务与话题的区别

ROS2中有两种主要的通信方式：
- **话题（Topic）**：异步、多对多通信
- **服务（Service）**：同步、一对一通信

## 创建服务

### 1. 定义服务接口

首先创建一个自定义服务接口：

```python
# tutorial_interfaces/srv/AddTwoInts.srv
int64 a
int64 b
---
int64 sum
```

### 2. 服务端实现

```python
import rclpy
from rclpy.node import Node
from tutorial_interfaces.srv import AddTwoInts

class AddTwoIntsServer(Node):
    def __init__(self):
        super().__init__('add_two_ints_server')
        self.srv = self.create_service(
            AddTwoInts, 
            'add_two_ints', 
            self.add_two_ints_callback
        )

    def add_two_ints_callback(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info(f'Incoming request: a={request.a} b={request.b}')
        return response

def main(args=None):
    rclpy.init(args=args)
    node = AddTwoIntsServer()
    rclpy.spin(node)
    rclpy.shutdown()
```

### 3. 客户端实现

```python
import rclpy
from rclpy.node import Node
from tutorial_interfaces.srv import AddTwoInts
import sys

class AddTwoIntsClient(Node):
    def __init__(self):
        super().__init__('add_two_ints_client')
        self.cli = self.create_client(AddTwoInts, 'add_two_ints')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting...')
        self.req = AddTwoInts.Request()

    def send_request(self, a, b):
        self.req.a = a
        self.req.b = b
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

def main(args=None):
    rclpy.init(args=args)
    node = AddTwoIntsClient()
    response = node.send_request(int(sys.argv[1]), int(sys.argv[2]))
    node.get_logger().info(f'Result: {response.sum}')
    rclpy.shutdown()
```

## 使用方法

```bash
# 启动服务端
ros2 run tutorial_package add_two_ints_server

# 启动客户端
ros2 run tutorial_package add_two_ints_client 3 5
```

## 服务调试

```bash
# 查看可用服务
ros2 service list

# 查看服务接口
ros2 service type /add_two_ints

# 命令行调用服务
ros2 service call /add_two_ints tutorial_interfaces/srv/AddTwoInts "{a: 1, b: 2}"
```

服务通信是ROS2中实现同步交互的重要方式，适用于需要即时响应的场景。
''',
            'category': 'ROS2进阶',
            'author_id': admin_id
        },
        {
            'title': 'ROS2 Launch文件编写',
            'content': '''# ROS2 Launch文件编写

## Launch文件的作用

Launch文件用于：
- 同时启动多个节点
- 设置节点参数
- 配置节点间的重映射
- 管理复杂的机器人系统

## Python Launch文件

### 基础示例

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='talker'
        ),
        Node(
            package='demo_nodes_py',
            executable='listener',
            name='listener'
        )
    ])
```

### 高级配置

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

def generate_launch_description():
    # 声明参数
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )
    
    # 获取参数值
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    return LaunchDescription([
        use_sim_time_arg,
        
        # 机器人状态发布节点
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'use_sim_time': use_sim_time}]
        ),
        
        # 条件启动节点
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            condition=IfCondition(use_sim_time)
        ),
        
        # 启动外部进程
        ExecuteProcess(
            cmd=['ros2', 'bag', 'play', 'rosbag.bag'],
            output='screen'
        )
    ])
```

## XML Launch文件

```xml
<launch>
    <arg name="use_sim_time" default="false"/>
    
    <node pkg="robot_state_publisher" 
          exec="robot_state_publisher" 
          name="robot_state_publisher">
        <param name="use_sim_time" value="$(var use_sim_time)"/>
    </node>
    
    <node pkg="rviz2" 
          exec="rviz2" 
          name="rviz2" 
          if="$(var use_sim_time)"/>
</launch>
```

## 包含其他Launch文件

```python
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare('another_package'),
                    'launch',
                    'another_launch.py'
                ])
            ])
        )
    ])
```

## 运行Launch文件

```bash
# 运行Python launch文件
ros2 launch my_package my_launch.py

# 运行XML launch文件
ros2 launch my_package my_launch.xml

# 传递参数
ros2 launch my_package my_launch.py use_sim_time:=true
```

Launch文件是管理复杂ROS2系统的重要工具，合理使用能大大提高开发效率。
''',
            'category': 'ROS2工具',
            'author_id': admin_id
        }
    ]
    
    # 插入示例文档
    for doc in sample_documents:
        cursor.execute('''
            INSERT OR IGNORE INTO documents (title, content, category, author_id) 
            VALUES (?, ?, ?, ?)
        ''', (doc['title'], doc['content'], doc['category'], doc['author_id']))
    
    conn.commit()
    conn.close()
    print("示例数据初始化完成！")
    print("管理员账户：admin / admin123")
    print("用户账户：ros2_learner / user123")

if __name__ == '__main__':
    init_sample_data()