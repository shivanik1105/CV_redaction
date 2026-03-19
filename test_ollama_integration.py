    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    summary1 = """A Python Developer with 5 years of experience in product-based application development, demonstrating strong analytical and critical thinking skills. The candidate is adept at working in fast-paced, deadline-driven environments and has a proactive approach with a solid work ethic.

    Key technical skills include Python programming, microservices, REST APIs, cloud platforms (AWS, Azure, GCP, Terraform), and frameworks such as FastAPI, Flask, Django, and Pyspark. The candidate is also experienced with DevOps tools (Git, Jenkins, CI/CD, Kubernetes), databases (SQLite, PostgreSQL, SQL, MongoDB), and data analytics/visualization (Plotly Dash, Tableau). Professional experience highlights building automated analytics systems, cloud storage solutions, and robust backend/frontend architectures with a focus on user experience and advanced data visualization.

    The candidate’s recent work involves developing an automated analytics platform using Python, Django, and GCP, with responsibilities spanning journal abstraction, cloud file management, backend integration, and analytics dashboard creation."""

    summary2 = """Candidate Summary: Chirayu Yelane
    A proactive Python Developer with 5+ years of experience building scalable, product-based applications. Expertise spans backend development, cloud infrastructure, data analytics, and full-stack integration. Demonstrates strong analytical thinking, adaptability in fast-paced environments, and a commitment to delivering high-quality software solutions.
    Technical Skills: Python, JavaScript, HTML, CSS, SQL, Django, Flask, FastAPI, React.js, Streamlit, Plotly-Dash, AWS, Azure, GCP, Terraform, Kubernetes, Jenkins, CI/CD, Docker, PostgreSQL, MySQL, MongoDB, SQLite, Elasticsearch, PySpark, Git, JIRA, Rally, Azure DevOps, Microservices, REST APIs, Pydantic, Pickle, Tableau, Plotly, Seaborn, JMeter.
    Professional Experience: Springer Nature (Python Developer, Oct 2023–Present), Paytm (Software Engineer, Jun 2022–Aug 2023), Payas Systems (Software Engineer, Aug 2019–Apr 2022). Projects include automated journal abstraction, loyalty/marketing SaaS, and ML-based loan prediction.
    Key Strengths: End-to-end development, strong data engineering, ML model deployment, Agile/DevOps, excellent communication."""

    vectorizer = TfidfVectorizer().fit_transform([summary1, summary2])
    similarity = cosine_similarity(vectorizer[0:1], vectorizer[1:2])[0][0]
    print(f"Cosine similarity: {similarity*100:.2f}%")