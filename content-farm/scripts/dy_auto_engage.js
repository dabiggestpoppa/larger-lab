/**
 * Content Farm - 抖音 Auto-Engagement Script
 * Based on DeekeScript framework (ad-deeke)
 * 
 * This script automates engagement on 抖音 (Douyin):
 * - Auto-like videos in target niche
 * - AI-powered comments (via DeepSeek/Baidu Wenxin)
 * - Auto-follow target accounts
 * - Collect UIDs from comment sections
 * 
 * Usage: Deploy to Android device/emulator via DeekeScript runtime
 */

let tCommon = require("app/dy/Common");
let DyIndex = require("app/dy/Index");
let DySearch = require("app/dy/Search");
let DyUser = require("app/dy/User");
let DyVideo = require("app/dy/Video");
let DyComment = require("app/dy/Comment");
let storage = require("common/storage");
let machine = require("common/machine");
let statistics = require("common/statistics");

let task = {
    // Configuration
    config: {
        niche: "fitness",           // Target niche
        daily_like_limit: 200,      // Max likes per day
        daily_comment_limit: 50,    // Max comments per day
        daily_follow_limit: 30,     // Max follows per day
        keywords: ["健身", "减肥", "运动", "瘦身", "增肌"],  // Target keywords
        comment_templates: [
            "太棒了！收藏了 💪",
            "学到了，感谢分享！",
            "这个动作很实用 👍",
            "坚持就是胜利！",
            "博主说得对，已关注"
        ],
        run_hours: [9, 12, 15, 19, 21],  // Active hours
        sleep_between_actions: 3000,      // 3 seconds between actions
        sleep_between_videos: 5000,       // 5 seconds between videos
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
        let allFile = "log/log-content-farm-" + file + ".txt";
        Log.setFile(allFile);
    },

    testTask() {
        // Check if within active hours
        let currentHour = new Date().getHours();
        if (!this.config.run_hours.includes(currentHour)) {
            Log.log("Outside active hours, sleeping...");
            return 101; // Sleep code
        }

        // Check daily limits
        if (this.stats.likes >= this.config.daily_like_limit) {
            Log.log("Daily like limit reached");
            return 101;
        }

        // Main engagement loop
        Log.log("Starting engagement cycle...");
        
        // 1. Search for target content
        let keyword = this.config.keywords[Math.floor(Math.random() * this.config.keywords.length)];
        Log.log("Searching for: " + keyword);
        DyIndex.intoSearchPage();
        tCommon.sleep(2000);
        
        // 2. Process search results
        let videos = DyVideo.getList();
        Log.log("Found " + videos.length + " videos");
        
        for (let i = 0; i < Math.min(videos.length, 10); i++) {
            // Check limits
            if (this.stats.likes >= this.config.daily_like_limit) break;
            if (this.stats.comments >= this.config.daily_comment_limit) break;
            
            // Like video (random chance to avoid pattern detection)
            if (Math.random() > 0.3) {
                DyVideo.like();
                this.stats.likes++;
                Log.log("Liked video " + (i + 1));
                tCommon.sleep(this.config.sleep_between_actions);
            }
            
            // Comment (lower frequency)
            if (Math.random() > 0.7 && this.stats.comments < this.config.daily_comment_limit) {
                let comment = this.getComment();
                if (comment) {
                    DyComment.send(comment);
                    this.stats.comments++;
                    Log.log("Commented: " + comment);
                    tCommon.sleep(this.config.sleep_between_actions);
                }
            }
            
            // Collect UIDs from comments
            if (Math.random() > 0.5) {
                let uids = DyComment.getUids();
                this.stats.uids_collected += uids.length;
                Log.log("Collected " + uids.length + " UIDs");
            }
            
            tCommon.sleep(this.config.sleep_between_videos);
        }
        
        // 3. Follow accounts (lowest frequency)
        if (Math.random() > 0.8 && this.stats.follows < this.config.daily_follow_limit) {
            DyUser.follow();
            this.stats.follows++;
            Log.log("Followed account");
        }
        
        // 4. Log statistics
        Log.log("Cycle complete. Stats: " + JSON.stringify(this.stats));
        statistics.save(this.stats);
        
        return 0;
    },

    getComment() {
        // Use AI-generated comment or template
        if (storage.get('setting_baidu_wenxin_switch', 'bool')) {
            return baiduWenxin.getComment("");
        }
        // Fallback to templates
        let templates = this.config.comment_templates;
        return templates[Math.floor(Math.random() * templates.length)];
    },
};

// Start accessibility mode
System.setAccessibilityMode('fast');
Engines.executeScript("unit/dialogClose.js");

// Main loop
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
                tCommon.sleep(60000); // Check every minute
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
