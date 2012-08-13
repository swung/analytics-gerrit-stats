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
    changes.status 
FROM 
    changes 
LEFT JOIN 
    patch_set_approvals 
ON 
    changes.change_id=patch_set_approvals.change_id 
WHERE 
    status !='A' -- EXCLUDE ABANDONDED CHANGE_SETS
AND
    status !='M' -- EXCLUDED MERGED CHANGE_SETS
AND NOT EXISTS 
    (SELECT * FROM changes WHERE change_id = patch_set_approvals.change_id) 
ORDER BY 
    created_on;

-- self-review gerrit-stats
SELECT 
    COUNT(changes.change_id) AS value, 
    changes.dest_project_name,
    -- changes.owner_account_id, 
    -- changes.created_on, 
    patch_set_approvals.granted AS granted_on
    -- patch_set_approvals.value 
    -- patch_set_approvals.account_id 
FROM 
    changes 
INNER JOIN 
    patch_set_approvals 
ON 
    changes.change_id=patch_set_approvals.change_id 
WHERE 
    value=2
AND 
    changes.dest_project_name='operations/puppet'
GROUP BY 
    DATE(patch_set_approvals.granted),
    changes.dest_project_name
ORDER BY 
    created_on;

-- total commits per day
CREATE TABLE commits AS
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
    DATE(changes.created_on),
    changes.dest_project_name
ORDER BY
    changes.created_on;


-- self-review
SELECT 
    COUNT(changes.change_id) AS value, 
    commits.commits,
    changes.dest_project_name,
    -- changes.owner_account_id, 
    changes.created_on
    -- patch_set_approvals.granted AS granted_on
    -- patch_set_approvals.value 
    -- patch_set_approvals.account_id 
FROM 
    changes
INNER JOIN 
    patch_set_approvals 
ON 
    changes.change_id=patch_set_approvals.change_id 
INNER JOIN
    commits
ON
    changes.dest_project_name=commits.dest_project_name
WHERE 
    value=2
AND
    changes.owner_account_id=patch_set_approvals.account_id
AND 
    changes.dest_project_name LIKE 'mediawiki/extensions/%'
AND
    DATE(commits.created_on)=DATE(changes.created_on)
GROUP BY 
    DATE(patch_set_approvals.granted),
    changes.dest_project_name
ORDER BY 
    changes.created_on;

-- ALL
SELECT 
    *
FROM
    changes
INNER JOIN
    accounts
ON
    changes.owner_account_id=accounts.account_id
WHERE
    change_id=3694
ORDER BY
    changes.created_on;

SELECT
    *
FROM 
    patch_set_approvals
INNER JOIN
    accounts
ON 
    patch_set_approvals.account_id=accounts.account_id
WHERE
    change_id=3694

ORDER BY
    patch_set_approvals.granted;


SELECT
                        *
                    FROM 
                        patch_set_approvals
                    INNER JOIN
                        accounts
                    ON 
                        patch_set_approvals.account_id=accounts.account_id
                    WHERE
                        patch_set_approvals.granted >= 2011-09-07
                    ORDER BY
                        patch_set_approvals.granted;