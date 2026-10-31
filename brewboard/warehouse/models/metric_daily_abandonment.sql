-- Daily cart abandonment, per store. Feeds the "Abandonment" tile on the ops dashboard.
-- abandoned = a cart that never became an order.
with carts_scored as (
  select
    store_id,
    substr(created_at, 1, 10) as day,
    converted,
    (julianday(last_activity_at) - julianday(created_at)) * 86400 as open_seconds
  from carts
)
select
  day,
  store_id,
  count(*) as carts,
  sum(case when converted = 0 then 1 else 0 end) as abandoned,
  round(1.0 * sum(case when converted = 0 then 1 else 0 end) / count(*), 4) as rate
from carts_scored
where open_seconds >= 60  -- drop bounces
group by day, store_id
order by day, store_id
