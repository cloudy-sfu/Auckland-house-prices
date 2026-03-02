-- next_month: latest existed month + 1 month
-- to parse in Python, start_year = next_month // 12, start_month = next_month % 12 + 1
select s.suburb_id, max(year * 12 + month) as next_month
from suburbs s
left join crimes c on s.suburb_id = c.suburb_id
group by s.suburb_id
