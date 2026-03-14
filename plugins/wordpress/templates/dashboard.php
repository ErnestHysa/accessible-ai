<?php
/**
 * AccessibleAI Dashboard Template
 */

$score = get_option('accessible_ai_latest_score', null);
$last_scan = get_option('accessible_ai_last_scan', null);
$site_id = get_option('accessible_ai_site_id', '');
?>

<div class="wrap accessible-ai-dashboard">
    <h1>
        <span class="dashicons dashicons-universal-access-alt"></span>
        <?php esc_html_e('AccessibleAI Dashboard', 'accessible-ai'); ?>
    </h1>

    <?php if (empty($site_id)): ?>
        <div class="notice notice-warning">
            <p>
                <?php
                printf(
                    __('Please %sconnect your API key%s to start scanning.', 'accessible-ai'),
                    '<a href="' . admin_url('admin.php?page=accessible-ai-settings') . '">',
                    '</a>'
                );
                ?>
            </p>
        </div>
    <?php endif; ?>

    <div class="accessible-ai-cards" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px;">
        <!-- Score Card -->
        <div class="card" style="background: #fff; padding: 20px; border: 1px solid #ccd0d4; box-shadow: 0 1px 1px rgba(0,0,0,.04);">
            <h2 style="margin-top: 0;"><?php esc_html_e('Accessibility Score', 'accessible-ai'); ?></h2>
            <?php if ($score !== null): ?>
                <div class="score-display" style="text-align: center; padding: 20px 0;">
                    <div class="score-number" style="font-size: 64px; font-weight: bold; color: <?php echo $score >= 90 ? '#22c55e' : ($score >= 70 ? '#eab308' : '#ef4444'); ?>;">
                        <?php echo esc_html($score); ?>
                    </div>
                    <div class="score-label" style="font-size: 18px; margin-top: 10px;">
                        <?php
                        $labels = array(
                            'excellent' => __('Excellent!', 'accessible-ai'),
                            'good' => __('Good Progress', 'accessible-ai'),
                            'fair' => __('Needs Work', 'accessible-ai'),
                            'poor' => __('Critical Issues', 'accessible-ai'),
                        );
                        $label = $score >= 90 ? 'excellent' : ($score >= 70 ? 'good' : ($score >= 50 ? 'fair' : 'poor'));
                        echo esc_html($labels[$label]);
                        ?>
                    </div>
                </div>
            <?php else: ?>
                <p><?php esc_html_e('No scan data yet.', 'accessible-ai'); ?></p>
            <?php endif; ?>
            <p style="text-align: center; margin-top: 15px;">
                <a href="<?php echo admin_url('admin.php?page=accessible-ai-scans'); ?>" class="button">
                    <?php esc_html_e('View Details', 'accessible-ai'); ?>
                </a>
            </p>
        </div>

        <!-- Quick Actions -->
        <div class="card" style="background: #fff; padding: 20px; border: 1px solid #ccd0d4; box-shadow: 0 1px 1px rgba(0,0,0,.04);">
            <h2 style="margin-top: 0;"><?php esc_html_e('Quick Actions', 'accessible-ai'); ?></h2>
            <div class="actions" style="display: flex; flex-direction: column; gap: 10px; margin-top: 15px;">
                <button id="accessible-ai-quick-scan" class="button button-primary button-large" style="text-align: center;">
                    <span class="dashicons dashicons-search" style="margin-top: 4px;"></span>
                    <?php esc_html_e('Run Scan', 'accessible-ai'); ?>
                </button>
                <a href="<?php echo admin_url('admin.php?page=accessible-ai-scans'); ?>" class="button button-large" style="text-align: center;">
                    <?php esc_html_e('View All Scans', 'accessible-ai'); ?>
                </a>
                <a href="<?php echo admin_url('admin.php?page=accessible-ai-settings'); ?>" class="button button-large" style="text-align: center;">
                    <?php esc_html_e('Settings', 'accessible-ai'); ?>
                </a>
            </div>
        </div>

        <!-- Status -->
        <div class="card" style="background: #fff; padding: 20px; border: 1px solid #ccd0d4; box-shadow: 0 1px 1px rgba(0,0,0,.04);">
            <h2 style="margin-top: 0;"><?php esc_html_e('Status', 'accessible-ai'); ?></h2>
            <table class="widefat" style="margin-top: 15px; border: 0;">
                <tr style="border: 0;">
                    <td style="border: 0;"><strong><?php esc_html_e('Connected Site', 'accessible-ai'); ?>:</strong></td>
                    <td style="border: 0;">
                        <?php if ($site_id): ?>
                            <span class="dashicons dashicons-yes" style="color: green;"></span>
                            <?php esc_html_e('Connected', 'accessible-ai'); ?>
                        <?php else: ?>
                            <span class="dashicons dashicons-no" style="color: red;"></span>
                            <?php esc_html_e('Not Connected', 'accessible-ai'); ?>
                        <?php endif; ?>
                    </td>
                </tr>
                <tr style="border: 0;">
                    <td style="border: 0;"><strong><?php esc_html_e('Last Scan', 'accessible-ai'); ?>:</strong></td>
                    <td style="border: 0;">
                        <?php if ($last_scan): ?>
                            <?php echo esc_html(date_i18n(get_option('date_format') . ' ' . get_option('time_format'), strtotime($last_scan))); ?>
                        <?php else: ?>
                            <?php esc_html_e('Never', 'accessible-ai'); ?>
                        <?php endif; ?>
                    </td>
                </tr>
                <tr style="border: 0;">
                    <td style="border: 0;"><strong><?php esc_html_e('Auto-Scan', 'accessible-ai'); ?>:</strong></td>
                    <td style="border: 0;">
                        <?php
                        $auto_scan = get_option('accessible_ai_auto_scan', 'weekly');
                        echo esc_html(ucfirst($auto_scan));
                        ?>
                    </td>
                </tr>
            </table>
        </div>
    </div>

    <!-- Recent Issues -->
    <div class="recent-issues" style="margin-top: 30px;">
        <h2><?php esc_html_e('Recent Issues Found', 'accessible-ai'); ?></h2>
        <div id="accessible-ai-recent-issues" class="accessible-ai-issues-list">
            <p class="spinner is-active" style="float: none; margin: 20px auto;"></p>
        </div>
    </div>
</div>

<script>
jQuery(document).ready(function($) {
    // Quick scan button
    $('#accessible-ai-quick-scan').on('click', function() {
        var $button = $(this);
        var $text = $button.find('.button-text');

        $button.prop('disabled', true);
        if (!$text.length) {
            $button.wrapInner('<span class="button-text"></span>');
        }

        $.ajax({
            url: ajaxurl,
            type: 'POST',
            data: {
                action: 'accessible_ai_run_scan',
                nonce: accessibleAI.nonce,
                full_scan: false
            },
            success: function(response) {
                if (response.success) {
                    $button.html('<span class="dashicons dashicons-update-alt spinning"></span> <?php esc_html_e('Scanning...', 'accessible-ai'); ?>');

                    // Poll for results
                    pollScan(response.data.scan_id);
                } else {
                    alert('<?php esc_html_e('Failed to start scan', 'accessible-ai'); ?>');
                    $button.prop('disabled', false);
                }
            },
            error: function() {
                alert('<?php esc_html_e('Failed to start scan', 'accessible-ai'); ?>');
                $button.prop('disabled', false);
            }
        });
    });

    function pollScan(scanId) {
        var attempts = 0;
        var maxAttempts = 60;

        var interval = setInterval(function() {
            attempts++;

            $.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'accessible_ai_get_scan_results',
                    nonce: accessibleAI.nonce,
                    scan_id: scanId
                },
                success: function(response) {
                    if (response.data.status === 'completed') {
                        clearInterval(interval);
                        location.reload();
                    } else if (response.data.status === 'failed') {
                        clearInterval(interval);
                        alert('<?php esc_html_e('Scan failed', 'accessible-ai'); ?>');
                        $('#accessible-ai-quick-scan').prop('disabled', false).text('<?php esc_html_e('Run Scan', 'accessible-ai'); ?>');
                    } else if (attempts >= maxAttempts) {
                        clearInterval(interval);
                        alert('<?php esc_html_e('Scan timed out', 'accessible-ai'); ?>');
                        $('#accessible-ai-quick-scan').prop('disabled', false).text('<?php esc_html_e('Run Scan', 'accessible-ai'); ?>');
                    }
                }
            });
        }, 5000);
    }

    // Load recent issues
    function loadRecentIssues() {
        $('#accessible-ai-recent-issues').html('<p class="spinner is-active" style="float: none; margin: 20px auto;"></p>');

        $.ajax({
            url: ajaxurl,
            type: 'GET',
            data: {
                action: 'accessible_ai_get_recent_issues',
                nonce: accessibleAI.nonce
            },
            success: function(response) {
                if (response.success && response.data.issues.length > 0) {
                    renderIssues(response.data.issues);
                } else {
                    $('#accessible-ai-recent-issues').html('<p><?php esc_html_e('No recent issues found.', 'accessible-ai'); ?></p>');
                }
            },
            error: function() {
                $('#accessible-ai-recent-issues').html('<p><?php esc_html_e('Failed to load issues.', 'accessible-ai'); ?></p>');
            }
        });
    }

    function renderIssues(issues) {
        var html = '<table class="widefat striped"><thead><tr>';
        html += '<th><?php esc_html_e('Severity', 'accessible-ai'); ?></th>';
        html += '<th><?php esc_html_e('Issue', 'accessible-ai'); ?></th>';
        html += '<th><?php esc_html_e('Location', 'accessible-ai'); ?></th>';
        html += '<th><?php esc_html_e('Action', 'accessible-ai'); ?></th>';
        html += '</tr></thead><tbody>';

        issues.forEach(function(issue) {
            var severityClass = issue.severity === 'critical' ? 'red' : (issue.severity === 'serious' ? 'orange' : 'yellow');
            html += '<tr>';
            html += '<td><span class="severity-badge severity-' + severityClass + '">' + issue.severity + '</span></td>';
            html += '<td>' + issue.description + '</td>';
            html += '<td><code>' + issue.selector + '</code></td>';
            html += '<td><button class="button button-small view-fix" data-issue-id="' + issue.id + '"><?php esc_html_e('View Fix', 'accessible-ai'); ?></button></td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
        $('#accessible-ai-recent-issues').html(html);
    }

    loadRecentIssues();
});
</script>
