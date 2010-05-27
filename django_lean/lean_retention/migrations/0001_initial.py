
from south.db import db
from django.db import models
from django_lean.lean_retention.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'LastActivity'
        db.create_table('lean_retention_lastactivity', (
            ('id', orm['lean_retention.LastActivity:id']),
            ('user', orm['lean_retention.LastActivity:user']),
            ('site', orm['lean_retention.LastActivity:site']),
            ('datetime', orm['lean_retention.LastActivity:datetime']),
            ('medium', orm['lean_retention.LastActivity:medium']),
        ))
        db.send_create_signal('lean_retention', ['LastActivity'])
        
        # Adding model 'SignIn'
        db.create_table('lean_retention_signin', (
            ('id', orm['lean_retention.SignIn:id']),
            ('user', orm['lean_retention.SignIn:user']),
            ('site', orm['lean_retention.SignIn:site']),
            ('datetime', orm['lean_retention.SignIn:datetime']),
            ('medium', orm['lean_retention.SignIn:medium']),
        ))
        db.send_create_signal('lean_retention', ['SignIn'])
        
        # Creating unique_together for [user, site, medium] on LastActivity.
        db.create_unique('lean_retention_lastactivity', ['user_id', 'site_id', 'medium'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [user, site, medium] on LastActivity.
        db.delete_unique('lean_retention_lastactivity', ['user_id', 'site_id', 'medium'])
        
        # Deleting model 'LastActivity'
        db.delete_table('lean_retention_lastactivity')
        
        # Deleting model 'SignIn'
        db.delete_table('lean_retention_signin')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'lean_retention.lastactivity': {
            'Meta': {'unique_together': "(['user', 'site', 'medium'],)"},
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'medium': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1L', 'to': "orm['sites.Site']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'lean_retention.signin': {
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'medium': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1L', 'to': "orm['sites.Site']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }
    
    complete_apps = ['lean_retention']
