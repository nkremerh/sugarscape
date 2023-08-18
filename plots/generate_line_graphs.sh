plottingScripts=( plot_agent_wealth_collected.plg plot_agent_wealth_total.plg plot_mean_time_to_live_age_limited.plg plot_mean_time_to_live.plg plot_percent_population_growth.plg plot_population_per_timestep.plg plot_starvation_deaths.plg plot_total_wealth.plg plot_wealth_collected.plg plot_agent_wealth_total_div_by_pop.plg plot_agent_wealth_collected_div_by_pop.plg plot_agent_tot_met_div_by_env_wealth_created.plg)

python "parse_logs.py" -p "../data/" -l line_graphs.dat

for ((graphIndex=0; graphIndex<"${#plottingScripts[@]}"; graphIndex++))
do
    gnuplot -c ${plottingScripts[$graphIndex]} 'line_graphs.dat'
done
