/**
 * Content Farm - 小红书 (Xiaohongshu) Auto-Engagement Script
 * Based on DeekeScript framework
 * 
 * Automates engagement on 小红书:
 * - Auto-like notes in target niche
 * - AI-powered comments
 * - Auto-follow creators
 * - Collect UIDs from comment sections
 */

let tCommon = require("app/xhs/Common");
let XhsIndex = require("app/xhs/Index");
let XhsSearch = require("app/xhs/Search");
let XhsUser = require("app/xhs/User");
let XhsNote = require("app/xhs/Note");
let XhsComment = require("app/xhs/Comment");
let storage = require("common/storage");
let machine = require("common/machine");
let statistics = require("common/statistics");

let task = {
    config: {
        niche: "lifestyle",
        daily_like_limit: 150,
        daily_comment_limit: 40,
        daily_follow_limit: 20,
        keywords: ["好物分享", "穿搭", "护肤", "美食", "旅行"],
        comment_templates: [
            "好棒！已收藏 ❤️",
            "太实用了，感谢分享！",
            "种草了，马上去买 🛒",
            "博主好会选！",
            "学到了，已关注 👍"
        ],
        run_hours: [9, 12, 15, 19, 21],
        sleep_between_actions: 3000,
        sleep_between_notes: 5000,
    },

    index: -1,
    stats: {
        likes: 0,
        comments: 0,
        follows: 0,
        uids_collected: 0,
    },

    run() {
        return this.testTask();
    },

    log() {
        let d = new Date();
        let file = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate();
        let allFile = "log/log-xhs-farm-" + file + ".txt";
        Log.setFile(allFile);
    },

    testTask() {
        let currentHour = new Date().getHours();
        if (!this.config.run_hours.includes(currentHour)) {
            Log.log("Outside active hours, sleeping...");
            return 101;
        }

        if (this.stats.likes >= this.config.daily_like_limit) {
            Log.log("Daily like limit reached");
            return 101;
        }

        Log.log("Starting XHS engagement cycle...");
        
        let keyword = this.config.keywords[Math.floor(Math.random() * this.config.keywords.length)];
        Log.log("Searching for: " + keyword);
        XhsIndex.intoSearchPage();
        tCommon.sleep(2000);
        
        let notes = XhsNote.getList();
        Log.log("Found " + notes.length + " notes");
        
        for (let i = 0; i < Math.min(notes.length, 10); i++) {
            if (this.stats.likes >= this.config.daily_like_limit) break;
            if (this.stats.comments >= this.config.daily_comment_limit) break;
            
            // Like note
            if (Math.random() > 0.3) {
                XhsNote.like();
                this.stats.likes++;
                Log.log("Liked note " + (i + 1));
                tCommon.sleep(this.config.sleep_between_actions);
            }
            
            // Comment
            if (Math.random() > 0.7 && this.stats.comments < this.config.daily_comment_limit) {
                let comment = this.getComment();
                if (comment) {
                    XhsComment.send(comment);
                    this.stats.comments++;
                    Log.log("Commented: " + comment);
                    tCommon.sleep(this.config.sleep_between_actions);
                }
            }
            
            // Collect UIDs
            if (Math.random() > 0.5) {
                let uids = XhsComment.getUids();
                this.stats.uids_collected += uids.length;
                Log.log("Collected " + uids.length + " UIDs");
            }
            
            tCommon.sleep(this.config.sleep_between_notes);
        }
        
        // Follow
        if (Math.random() > 0.8 && this.stats.follows < this.config.daily_follow_limit) {
            XhsUser.follow();
            this.stats.follows++;
            Log.log("Followed creator");
        }
        
        Log.log("Cycle complete. Stats: " + JSON.stringify(this.stats));
        statistics.save(this.stats);
        
        return 0;
    },

    getComment() {
        if (storage.get('setting_baidu_wenxin_switch', 'bool')) {
            return baiduWenxin.getComment("");
        }
        let templates = this.config.comment_templates;
        return templates[Math.floor(Math.random() * templates.length)];
    },
};

System.setAccessibilityMode('fast');
Engines.executeScript("unit/dialogClose.js");

while (true) {
    task.log();
    try {
        tCommon.openApp();
        let code = task.run();
        if (code === 101) {
            FloatDialogs.toast('Resting...');
            Log.log('Resting until next active hour');
            tCommon.backApp();
            while (true) {
                tCommon.sleep(60000);
                let hour = new Date().getHours();
                if (task.config.run_hours.includes(hour)) {
                    break;
                }
            }
            throw new Error('Re-entering active hours');
        }
        tCommon.sleep(3000);
    } catch (e) {
        Log.log("Error: " + e);
        tCommon.closeAlert(1);
        System.setAccessibilityMode('fast');
        tCommon.backHome();
    }
}
