# Fudan_Sportscourt_Order
简陋的使用说明
==============
同步文件
--------
将本Repository的文件clone到本地，不会的话自行搜索git clone的用法，不是我不教而是我也不会。实在不行直接从github复制文件到本地也行，凑合用。

驱动和库安装
------------
假设你安装过python，没装的搜一下怎么装。然后下载浏览器驱动到python的安装路径（依然参考百度）。通过pip 安装selennium、requests、opencv等库，可能还需要别的，若运行时提示缺少部分库自己装一下。

auto run 脚本和config文件
-------------------------
新建一个目录，不建议直接在仓库里面直接搞这些事情，否则通过git clone同步更新的时候会覆盖config信息。把仓库中的config文件复制过来，把账号密码和IYUU token内容改成自己的。
尖括号要去掉！！！IYUU token可以百度搜索爱语飞飞，然后微信扫码获取，用来接收预定信息。
新建一个run.bat文件（本质上是一个文本文件，可以新建txt然后重命名）。内容是py.exe /仓库位置/python文件名。如果是需要自动预定周一周四的活动场地python文件选order不要选pickup。

设置定时任务
-----------
设置一个定时任务，定时启动这个run.bat。一般设置为每周六和周二的上午6：59：40执行即可。电脑的定时睡眠等功能关掉。