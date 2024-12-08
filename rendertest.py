import argparse
from playwright.sync_api import sync_playwright
import asyncio
import time
import concurrent.futures
import pandas as pd
from datetime import datetime
import statistics
import random

class StreamlitLoadTest:
    def __init__(self, url="http://192.168.31.8:8501/"):
        self.url = url
        self.metrics = []
        

    def run_single_user_test(self, user_id):
        with sync_playwright() as p:
            # Create a new browser context for each user (isolated session)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(0)  # Applies to all actions
            page.set_default_navigation_timeout(0)  # For navigation-specific timeouts

            metrics = {'user_id': user_id}
            
            try:
                # Measure navigation time
                start_time = time.time()
                response = page.goto(self.url)
                navigation_time = time.time() - start_time
                
                # Wait for main content
                page.wait_for_selector("h1:has-text('Claim Report Dashboard Testing')")
                render_time = time.time() - start_time
                
                # Simulate unique user behavior
                filter_start = time.time()
               
                page.wait_for_selector("text=Filtered Claims Statistics")
                
                filter_time = time.time() - filter_start
                
                # Get performance metrics
                perf_metrics = page.evaluate("""() => {
                    const timing = window.performance.timing;
                    return {
                        ttfb: timing.responseStart - timing.navigationStart,
                        fcp: performance.getEntriesByName('first-contentful-paint')[0]?.startTime,
                        tti: timing.domInteractive - timing.navigationStart
                    }
                }""")
                
                metrics.update({
                    'timestamp': datetime.now(),
                    'navigation_time': navigation_time,
                    'render_time': render_time,
                    'filter_time': filter_time,
                    'ttfb': perf_metrics['ttfb'],
                    'fcp': perf_metrics['fcp'],
                    'tti': perf_metrics['tti'],
                    'status_code': response.status if response else None,
                   
                })
            
            except Exception as e:
                print(f"Error for user {user_id}: {str(e)}")
                metrics.update({
                    'timestamp': datetime.now(),
                    'error': str(e),
                    'status_code': 500
                })
            
            finally:
                context.close()
                browser.close()
                
            return metrics

    def run_concurrent_users(self, num_users=3):
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(self.run_single_user_test, f"user_{i}") 
                      for i in range(num_users)]
            results = [f.result() for f in futures]
            self.metrics.extend(results)

    def generate_report(self):
        df = pd.DataFrame(self.metrics)
        
        report = {
            'Total Users': len(df),
            'Unique Users': df['user_id'].nunique(),
            'Avg Navigation Time': statistics.mean(df['navigation_time']),
            'Avg Render Time': statistics.mean(df['render_time']),
            'Avg Filter Time': statistics.mean(df['filter_time']),
            'Avg TTFB': statistics.mean(df['ttfb']),
            'Avg FCP': statistics.mean(df['fcp']),
            'Avg TTI': statistics.mean(df['tti']),
            '95th Percentile Render Time': df['render_time'].quantile(0.95),
            'Success Rate': (df['status_code'] == 200).mean() * 100
        }
        
        # Add user behavior analysis
        if 'claim_number' in df.columns:
            report['Unique Claim Numbers'] = df['claim_number'].nunique()
            report['Most Common System'] = df['system'].mode().iloc[0]
        
        return report

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run load test for Streamlit application')
    parser.add_argument(
        '--users', 
        type=int,
        default=10,
        help='Number of concurrent users to simulate (default: 10)'
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    if args.users < 1:
        print("Error: Number of users must be at least 1")
        return
        
    load_test = StreamlitLoadTest()
    
    print(f"Starting load test with {args.users} concurrent users...")
    load_test.run_concurrent_users(num_users=args.users)
    
    print("\nTest Results:")
    report = load_test.generate_report()
    for metric, value in report.items():
        if isinstance(value, (int, float)):
            print(f"{metric}: {value:.2f}")
        else:
            print(f"{metric}: {value}")

if __name__ == "__main__":
    main()