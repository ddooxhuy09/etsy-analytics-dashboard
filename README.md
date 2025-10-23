# 🚀 Etsy Analytics Dashboard - Streamlit Cloud Deployment

## 📋 Tổng quan
Folder này chứa tất cả files cần thiết để deploy Etsy Analytics Dashboard lên **Streamlit Community Cloud**.

## 📁 Cấu trúc thư mục
```
streamlit_cloud_deploy/
├── main.py                          # Main entry point
├── requirements.txt                 # Python dependencies
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── src/
│   └── analytics/
│       ├── utils/
│       │   └── postgres_connection.py
│       └── dashboard/
│           ├── charts/             # All chart functions
│           └── profit_loss_statement/
└── README.md                       # This file
```

## 🚀 Cách deploy lên Streamlit Cloud

### Bước 1: Upload lên GitHub
```bash
# 1. Tạo repository mới trên GitHub
# 2. Clone repository về máy
git clone https://github.com/yourusername/etsy-dashboard.git
cd etsy-dashboard

# 3. Copy tất cả files từ streamlit_cloud_deploy/ vào repository
# 4. Commit và push
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main
```

### Bước 2: Deploy trên Streamlit Cloud
1. **Vào [share.streamlit.io](https://share.streamlit.io)**
2. **Đăng nhập bằng GitHub**
3. **Click "New app"**
4. **Chọn repository**: `yourusername/etsy-dashboard`
5. **Set main file**: `main.py`
6. **Click "Deploy!"**

### Bước 3: Cấu hình Secrets
Trong Streamlit Cloud dashboard:
1. **Vào Settings → Secrets**
2. **Thêm các secrets sau:**

```toml
[secrets]
POSTGRES_HOST = "aws-1-ap-southeast-1.pooler.supabase.com"
POSTGRES_PORT = "6543"
POSTGRES_DB = "postgres"
POSTGRES_USER = "postgres.ltnxbmqzguhwwilvxfaj"
POSTGRES_PASSWORD = "mAdJUW85WcoYJiCc"
POSTGRES_URL = "postgresql://postgres.ltnxbmqzguhwwilvxfaj:mAdJUW85WcoYJiCc@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
```

## 🔧 Cấu hình Database

### Supabase Connection
- **Host**: `aws-1-ap-southeast-1.pooler.supabase.com`
- **Port**: `6543`
- **Database**: `postgres`
- **User**: `postgres.ltnxbmqzguhwwilvxfaj`
- **Password**: `mAdJUW85WcoYJiCc`

### Connection String
```
postgresql://postgres.ltnxbmqzguhwwilvxfaj:mAdJUW85WcoYJiCc@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
```

## 📊 Features

### Dashboard Tab
- 📈 **Key Performance Indicators**: Revenue, Orders, Customers, AOV
- 📊 **Revenue & Profit Analysis**: Monthly trends
- 👥 **Customer Analysis**: New vs Returning customers
- 🌍 **Geographic Analysis**: Customer locations
- 🛍️ **Product Performance**: Top selling products
- 📊 **Customer Metrics**: CAC, CLV, Retention
- 📈 **Orders Analysis**: Monthly order trends
- 💰 **AOV Over Time**: Average order value trends
- 📊 **Revenue Comparison**: Year-over-year comparison
- ⚖️ **CAC/CLV Ratio**: Customer acquisition efficiency

### Profit & Loss Statement Tab
- 💰 **Revenue Breakdown**: Detailed revenue analysis
- 💸 **Expense Analysis**: Cost breakdown
- 📊 **Profit Margins**: Net profit calculations
- 📈 **Trends**: Monthly profit/loss trends

### Account Statement Tab
- 🏦 **Bank Account Overview**: All bank accounts summary
- 💳 **Transaction Details**: Detailed transaction history
- 📊 **Account Balances**: Current and historical balances
- 📄 **PDF Export**: Generate account statements
- 🔍 **Filter & Search**: Advanced filtering options

## 🎯 Ưu điểm của Streamlit Cloud

- ✅ **Hoàn toàn miễn phí**
- ✅ **Zero configuration** - Không cần Docker
- ✅ **Auto-deploy** khi push code
- ✅ **Built-in security** với secrets
- ✅ **Easy sharing** - Chia sẻ link dễ dàng
- ✅ **Mobile-friendly** - Responsive design
- ✅ **Real-time updates** - Auto-refresh data

## 🔄 Auto-deploy

Mỗi khi bạn push code lên GitHub:
- Streamlit Cloud tự động detect changes
- Tự động rebuild và deploy
- Không cần làm gì thêm!

## 📱 Mobile Support

Dashboard được tối ưu cho mobile:
- Responsive design
- Touch-friendly interface
- Optimized charts cho mobile

## 🆘 Troubleshooting

### App không start
- Kiểm tra `requirements.txt`
- Kiểm tra main file path
- Kiểm tra logs trong Streamlit Cloud dashboard

### Database connection error
- Kiểm tra secrets configuration
- Đảm bảo Supabase cho phép external connections
- Test connection string

### Performance issues
- Streamlit Cloud có giới hạn resources
- Consider optimize queries
- Monitor memory usage

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra logs trong Streamlit Cloud dashboard
2. Đảm bảo database connection
3. Kiểm tra environment variables
4. Test local trước khi deploy

## 🎉 Kết quả

Sau khi deploy thành công:
- ✅ Dashboard chạy 24/7 trên cloud
- ✅ Không cần máy tính của bạn
- ✅ Tự động restart khi có lỗi
- ✅ Có thể truy cập từ bất kỳ đâu
- ✅ Kết nối trực tiếp với Supabase database
- ✅ Chia sẻ link dễ dàng

## 🔗 Links

- **Streamlit Cloud**: https://share.streamlit.io
- **Supabase**: https://supabase.com
- **Documentation**: https://docs.streamlit.io
