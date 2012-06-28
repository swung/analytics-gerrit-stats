-- Written by Diederik van Liere (dvanliere@wikimedia.org)
-- For testing gerrit-stats queries

-- Desired output
-- change_id, repo, submitter, date_created, date_approved, approval, approved_by
-- Tables required: Changes, Patch_set_approvals

-- QUERIeS

-- +2 query
SELECT 
    changes.change_id, 
    changes.dest_project_name, 
    changes.owner_account_id, 
    changes.created_on, 
    patch_set_approvals.granted, 
    patch_set_approvals.value, 
    patch_set_approvals.account_id 
FROM 
    changes 
INNER JOIN 
    patch_set_approvals 
ON 
    changes.change_id=patch_set_approvals.change_id 
WHERE 
    value=2 
ORDER BY 
    created_on;


-- +1 query
SELECT  
    changes.change_id, 
    changes.dest_project_name, 
    changes.owner_account_id, 
    changes.created_on, 
    MIN(patch_set_approvals.granted), 
    patch_set_approvals.value, 
    patch_set_approvals.account_id 
FROM 
    changes
LEFT JOIN 
    patch_set_approvals 
ON 
    changes.change_id=patch_set_approvals.change_id 
WHERE 
    patch_set_approvals.value=1 
GROUP BY
    patch_set_approvals.change_id
ORDER BY 
    created_on;



-- no-review query
SELECT 
    changes.change_id, 
    changes.dest_project_name, 
    changes.owner_account_id, 
    changes.created_on, 
    patch_set_approvals.granted, 
    patch_set_approvals.value, 
    patch_set_approvals.account_id, 
    patch_set_approvals.status 
FROM 
    changes 
LEFT JOIN 
    patch_set_approvals 
ON 
    changes.change_id=Patch_set_approvals.change_id 
WHERE 
    status !='A' -- EXCLUDE ABANDONDED CHANGE_SETS
AND NOT EXISTS 
    (SELECT * FROM changes WHERE change_id = patch_set_approvals.change_id) 
ORDER BY 
    created_on;

-- total commits per day
SELECT
    changes.dest_project_name,
    changes.created_on,
    COUNT(changes.change_id) AS commits
FROM
    changes
WHERE
    DATE(changes.created_on) >= DATE('2009-09-07') -- This is the date of the first commit to Gerrit
AND
    DATE(changes.created_on) <= DATE('2014-12-31') -- This is an arbitrary future date, obviously if we still run this by that time then we need to adjust this date. 
GROUP BY
    DATE(changes.created_on)
ORDER BY
    changes.created_on;

