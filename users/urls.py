from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView
from django.urls import path
from .import views

urlpatterns=[
    path('login/',views.Login,name='login'),
    path('register/',views.Signup,name="signup"),
    path('activate/(<uidb64>[0-9A-Za-z_\-]+)/(<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', views.activate, name='activate'),
    path('update-profile/',views.UpdateProfile,name="update_profile"),
    path('reset-password',
         PasswordResetView.as_view(template_name='users/password_reset_form.html'), name='password_reset'),
    path('reset-password/done',
         PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset-password/confirm/<uidb64>[0-9A-Za-z]+)-<token>/',
         PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset-password/complete/',
         PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),


    path('password-change/',views.PasswordChange,name="passwordchange"),
    path('logout/',views.Logout,name="logout"),
    path('contract-us',views.ContactUs,name='contact'),
    path('contest-home/',views.ContestHome,name="contesthome"),
    path('view-contest/<int:id>',views.ViewContest,name="viewcontest"),
    path('contest/join',views.JoinContest,name="joincontest"),
    path('checkout/<str:pack>', views.Checkout, name="checkout"),
    path('subscription-complete',views.SubscriptionCompleted,name="scomplete"),
    path('upload/photo/<int:id>',views.UploadPhoto,name="uploadphoto"),
    path('contest/love',views.ContestLove,name="contestlove"),
    path('remove-photo/',views.RemovePhoto,name="removephoto"),
    path('decleare-winner/<int:contest>/<int:photom>',views.Winner,name="winner"),
    path('dashboard/',views.Dashboard,name="dashboard"),
    path('profile/',views.UserProfile,name="profile"),
    path('photo/update',views.PHotoUpdate,name="photoupdate"),
    path('add-contest/',views.AddCont,name="addcontest"),
    path('view-contest/',views.ManageContest,name="managecontest"),
    path('delete-contest/',views.DeleteContest,name="deletecontest"),
    path('update-contest/<int:id>',views.UpdateContest,name="updatecontest"),
    path('add-balance/',views.AddBalance,name="addbalance"),
    path('completed/',views.paymentComplated,name="completed"),
    path('request-payment/',views.RequestPayment,name="requestpayment"),
    path('gallary-view/',views.Galary,name="galary"),
    path('about-me/',views.AboutmeDetails,name='aboutme'),

    # Feedback url
    path('feedback/',views.FeedbackView,name='feedback'),
    ]
