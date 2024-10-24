import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline   
#from sklearn.metrics import classification_report
from sklearn import metrics

# Đọc dữ liệu từ file CSV
data = pd.read_csv('api/intent_data.csv')

# Chia dữ liệu thành tập huấn luyện và kiểm tra
X_train, X_test, y_train, y_test = train_test_split(data['text'], data['intent'], test_size=0.2, random_state=42)

# Tạo mô hình
model = make_pipeline(CountVectorizer(), MultinomialNB())

# Huấn luyện mô hình
model.fit(X_train, y_train)

# Dự đoán trên tập kiểm tra
predicted = model.predict(X_test)

# Đánh giá mô hình
accuracy = metrics.accuracy_score(y_test, predicted)
print(f'Accuracy: {accuracy:.2f}')

def get_intents_from_file(file_name):
    # Đọc dữ liệu từ file Excel
    df = pd.read_csv(file_name)
    
    # Lấy dữ liệu từ cột 'user'
    user_data = df['user'].tolist()  # Giả sử cột cần lấy là 'user'
    
    # Dự đoán intent cho từng câu trong cột 'user'
    predicted_intents = model.predict(user_data)  # Sử dụng mô hình đã huấn luyện
    
    return predicted_intents.tolist()
def get_intent_from_question(question):
    # Dự đoán intent cho câu hỏi
    predicted_intent = model.predict([question])
    return predicted_intent[0]