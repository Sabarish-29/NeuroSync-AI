import React, { useState } from 'react';
import { Navigation } from './components/shared/Navigation';
import { TeacherDashboard } from './components/teacher/Dashboard';
import { LearningInterface } from './components/student/LearningInterface';
import { ReadinessCheck } from './components/student/ReadinessCheck';
import { SpacedReview } from './components/student/SpacedReview';
import { KnowledgeMap } from './components/student/KnowledgeMap';

export type AppView =
  | 'teacher'
  | 'student'
  | 'readiness'
  | 'review'
  | 'knowledge';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>('teacher');
  const [studentId] = useState('student-001');
  const [lessonId] = useState('lesson-001');

  const renderView = () => {
    switch (currentView) {
      case 'teacher':
        return <TeacherDashboard />;
      case 'student':
        return (
          <LearningInterface
            studentId={studentId}
            lessonId={lessonId}
            videoUrl="/demo_videos/sample.mp4"
          />
        );
      case 'readiness':
        return (
          <ReadinessCheck
            studentId={studentId}
            lessonTopic="Photosynthesis"
            onComplete={() => setCurrentView('student')}
          />
        );
      case 'review':
        return <SpacedReview studentId={studentId} />;
      case 'knowledge':
        return <KnowledgeMap studentId={studentId} />;
      default:
        return <TeacherDashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-surface-dark">
      <Navigation currentView={currentView} onNavigate={setCurrentView} />
      <main className="pt-16">{renderView()}</main>
    </div>
  );
};

export default App;
