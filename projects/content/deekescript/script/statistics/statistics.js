var deekeStatistics = {
    getDate() {
        let d = new Date();
        let m = d.getMonth() + 1;
        let date = d.getDate();
        return (m >= 10 ? m : ('0' + m)) + '.' + (date >= 10 ? date : ('0' + date));
    },
    getData(time) {
        time = time || this.getDate();
        return {
            s_viewVideo: Storage.getInteger('s_viewVideo' + time) || 0,
            s_viewTargetVideo: Storage.getInteger('s_viewTargetVideo' + time) || 0,
            s_zan: Storage.getInteger('s_zan' + time) || 0,
            s_comment: Storage.getInteger('s_comment' + time) || 0,
            s_zanComment: Storage.getInteger('s_zanComment' + time) || 0,
            s_privateMsg: Storage.getInteger('s_privateMsg' + time) || 0,
            s_focus: Storage.getInteger('s_focus' + time) || 0,
            s_viewUser: Storage.getInteger('s_viewUser' + time) || 0,
        }
    },
    getWeekDate() {
        let dates = [];
        // 获取当前日期
        let now = new Date();
        // 循环获取最近 7 天的日期
        for (let i = 1; i <= 7; i++) {
            // 获取当前日期的时间戳
            let timestamp = now.getTime();
            // 计算 i 天前的时间戳
            let dayTimestamp = 24 * 60 * 60 * 1000; // 一天的毫秒数
            let iDayAgoTimestamp = timestamp - i * dayTimestamp;
            // 转换为日期对象
            let date = new Date(iDayAgoTimestamp);
            // 格式化日期为 "yyyy-MM-dd" 的字符串并存入数组
            //let year = date.getFullYear();
            let month = ("0" + (date.getMonth() + 1)).slice(-2);
            let day = ("0" + date.getDate()).slice(-2);
            dates.push(month + "." + day);
        }
        return dates;
    },

    getWeekData() {
        let dates = this.getWeekDate();
        let data = [];
        for (let i in dates) {
            data.push([dates[i], this.getData(dates[i])]);
        }

        //数据整理
        let res = [];
        let ids = ['s_viewVideo', 's_viewTargetVideo', 's_zan', 's_comment', 's_zanComment', 's_privateMsg', 's_focus', 's_viewUser'];
        for (let i in ids) {
            res[ids[i]] = [];
            for (let j = data.length - 1; j >= 0; j--) {
                res[ids[i]].push([data[j][0], data[j][1][ids[i]]]);
            }
        }
        return res;
    },

    dataList() {
        let data = this.getData(this.getDate());
        let weekData = this.getWeekData();
        //weight最大24
        return [
            {
                'title': '今日累计视频',
                'weight': 12,
                'checked': true,
                'value': data['s_viewVideo'],
                'data': weekData['s_viewVideo'],
            },
            {
                'title': '今日目标视频',
                'weight': 12,
                'value': data['s_viewTargetVideo'],
                'data': weekData['s_viewTargetVideo'],
            },
            {
                'title': '今日点赞',
                'weight': 8,
                'value': data['s_zan'],
                'data': weekData['s_zan'],
            },
            {
                'title': '今日评论',
                'count': 1,
                'weight': 8,
                'value': data['s_comment'],
                'data': weekData['s_comment'],
            },
            {
                'title': '今日赞评论',
                'weight': 8,
                'value': data['s_zanComment'],
                'data': weekData['s_zanComment'],
            },
            {
                'title': '今日私信',
                'weight': 8,
                'value': data['s_privateMsg'],
                'data': weekData['s_privateMsg'],
            },
            {
                'title': '今日关注',
                'count': 1,
                'weight': 8,
                'value': data['s_focus'],
                'data': weekData['s_focus'],
            },
            {
                'title': '今日访问',
                'weight': 8,
                'value': data['s_viewUser'],
                'data': weekData['s_viewUser'],
            },
        ];
    }
}
