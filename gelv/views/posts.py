from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from gelv.models import Post


class PostListView(ListView):
    model = Post
    paginate_by = 20
    template_name = 'posts/post-list.html'


class PostDetailView(DetailView):
    model = Post
    template_name = 'posts/post.html'
