/**
 * AccessibleAI Admin JavaScript
 */

(function($) {
    'use strict';

    // Run scan
    $('#accessible-ai-run-scan').on('click', function(e) {
        e.preventDefault();
        var $button = $(this);
        var fullScan = $button.data('full-scan') === true;

        $button.prop('disabled', true).html('<span class="dashicons dashicons-update-alt spinning"></span> Starting...');

        $.ajax({
            url: ajaxurl,
            type: 'POST',
            data: {
                action: 'accessible_ai_run_scan',
                nonce: accessibleAI.nonce,
                full_scan: fullScan
            },
            success: function(response) {
                if (response.success) {
                    $button.html('<span class="dashicons dashicons-update-alt spinning"></span> Scanning...');
                    startPolling(response.data.scan_id);
                } else {
                    alert('Failed to start scan: ' + (response.data.message || 'Unknown error'));
                    $button.prop('disabled', false).text('Run Scan');
                }
            },
            error: function() {
                alert('Failed to start scan. Please try again.');
                $button.prop('disabled', false).text('Run Scan');
            }
        });
    });

    // Poll for scan completion
    function startPolling(scanId) {
        var attempts = 0;
        var maxAttempts = 60;
        var progressBar = $('#accessible-ai-progress-bar');
        var progressText = $('#accessible-ai-progress-text');

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
                    if (response.data) {
                        var status = response.data.status;
                        var progress = Math.min(95, Math.round((attempts / maxAttempts) * 100));

                        if (progressBar.length) {
                            progressBar.find('.accessible-ai-scan-progress-fill').css('width', progress + '%').text(progress + '%');
                        }

                        if (status === 'completed') {
                            clearInterval(interval);
                            if (progressBar.length) {
                                progressBar.find('.accessible-ai-scan-progress-fill').css('width', '100%').text('Complete!');
                            }
                            showResults(response.data);
                        } else if (status === 'failed') {
                            clearInterval(interval);
                            alert('Scan failed: ' + (response.data.error_message || 'Unknown error'));
                            $('#accessible-ai-run-scan').prop('disabled', false).text('Run Scan');
                        } else if (attempts >= maxAttempts) {
                            clearInterval(interval);
                            alert('Scan timed out. Please try again.');
                            $('#accessible-ai-run-scan').prop('disabled', false).text('Run Scan');
                        }
                    }
                },
                error: function() {
                    if (attempts >= 3) {
                        clearInterval(interval);
                        alert('Failed to check scan status.');
                        $('#accessible-ai-run-scan').prop('disabled', false).text('Run Scan');
                    }
                }
            });
        }, 5000);
    }

    // Show scan results
    function showResults(scan) {
        $('#accessible-ai-run-scan').prop('disabled', false).text('Run Scan');

        // Update progress
        $('#accessible-ai-progress-bar').hide();
        $('#accessible-ai-results').show();

        // Update score
        if (scan.score !== null) {
            var scoreClass = scan.score >= 90 ? 'excellent' : (scan.score >= 70 ? 'good' : 'poor');
            $('#accessible-ai-score').text(scan.score).removeClass().addClass('score-number ' + scoreClass);
            $('#accessible-ai-score-label').text(scoreClass.charAt(0).toUpperCase() + scoreClass.slice(1));
        }

        // Load issues
        loadIssues(scan.id);
    }

    // Load issues for a scan
    function loadIssues(scanId) {
        $('#accessible-ai-issues-list').html('<p class="spinner is-active"></p>');

        $.ajax({
            url: ajaxurl,
            type: 'POST',
            data: {
                action: 'accessible_ai_get_scan_issues',
                nonce: accessibleAI.nonce,
                scan_id: scanId
            },
            success: function(response) {
                if (response.success && response.data.length > 0) {
                    renderIssues(response.data);
                } else {
                    $('#accessible-ai-issues-list').html('<p>No issues found!</p>');
                }
            }
        });
    }

    // Render issues table
    function renderIssues(issues) {
        var html = '<table class="widefat striped"><thead><tr>';
        html += '<th>Severity</th>';
        html += '<th>Issue</th>';
        html += '<th>Selector</th>';
        html += '<th>Action</th>';
        html += '</tr></thead><tbody>';

        issues.forEach(function(issue) {
            var severityClass = issue.severity;
            html += '<tr>';
            html += '<td><span class="severity-badge severity-' + severityClass + '">' + issue.severity + '</span></td>';
            html += '<td>' + escapeHtml(issue.description) + '</td>';
            html += '<td><code>' + escapeHtml(issue.selector || '') + '</code></td>';
            html += '<td><button class="button button-small accessible-ai-view-fix" data-issue-id="' + issue.id + '">View Fix</button></td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
        $('#accessible-ai-issues-list').html(html);
    }

    // View fix
    $(document).on('click', '.accessible-ai-view-fix', function() {
        var issueId = $(this).data('issue-id');
        var $modal = $('#accessible-ai-fix-modal');

        $modal.find('.accessible-ai-fix-modal-content pre').text('Loading fix...');

        $.ajax({
            url: ajaxurl,
            type: 'POST',
            data: {
                action: 'accessible_ai_get_fix',
                nonce: accessibleAI.nonce,
                issue_id: issueId
            },
            success: function(response) {
                if (response.success) {
                    $modal.find('.accessible-ai-fix-modal-content pre').text(response.data.fix_code || 'No fix available');
                    $modal.addClass('active');
                } else {
                    alert('Failed to get fix: ' + (response.data.message || 'Unknown error'));
                }
            }
        });
    });

    // Close fix modal
    $('#accessible-ai-fix-modal').on('click', function(e) {
        if (e.target === this) {
            $(this).removeClass('active');
        }
    });

    $('.accessible-ai-close-modal').on('click', function() {
        $('#accessible-ai-fix-modal').removeClass('active');
    });

    // Copy fix code
    $(document).on('click', '.accessible-ai-copy-fix', function() {
        var code = $(this).closest('.accessible-ai-fix-modal-content').find('pre').text();
        navigator.clipboard.writeText(code).then(function() {
            $('.accessible-ai-copy-fix').text('Copied!');
            setTimeout(function() {
                $('.accessible-ai-copy-fix').text('Copy to Clipboard');
            }, 2000);
        });
    });

    // Utility functions
    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Initialize
    $(document).ready(function() {
        // Load scan history on scans page
        if ($('#accessible-ai-scan-history').length) {
            loadScanHistory();
        }
    });

    function loadScanHistory() {
        $.ajax({
            url: ajaxurl,
            type: 'GET',
            data: {
                action: 'accessible_ai_get_scan_history',
                nonce: accessibleAI.nonce
            },
            success: function(response) {
                if (response.success && response.data.length > 0) {
                    renderScanHistory(response.data);
                } else {
                    $('#accessible-ai-scan-history').html('<p>No scans yet.</p>');
                }
            }
        });
    }

    function renderScanHistory(scans) {
        var html = '<table class="widefat striped"><thead><tr>';
        html += '<th>Date</th>';
        html += '<th>Score</th>';
        html += '<th>Issues</th>';
        html += '<th>Status</th>';
        html += '</tr></thead><tbody>';

        scans.forEach(function(scan) {
            var scoreColor = scan.score >= 90 ? 'green' : (scan.score >= 70 ? '#eab308' : 'red');
            var statusClass = scan.status;

            html += '<tr>';
            html += '<td>' + new Date(scan.created_at).toLocaleString() + '</td>';
            html += '<td><span style="color: ' + scoreColor + '; font-weight: bold;">' + (scan.score !== null ? scan.score : '-') + '</span></td>';
            html += '<td>' + (scan.total_issues || 0) + ' total</td>';
            html += '<td><span class="status-' + statusClass + '">' + scan.status + '</span></td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
        $('#accessible-ai-scan-history').html(html);
    }

})(jQuery);
